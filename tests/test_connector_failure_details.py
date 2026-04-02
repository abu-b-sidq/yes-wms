from __future__ import annotations

import httpx
import pytest

from app.connectors.enums import ConnectorType, SyncEntityType, SyncStatus
from app.connectors.exceptions import ConnectorTransportError
from app.connectors.models import ConnectorConfig, ExternalEntityMapping, SyncLog
from app.connectors.providers.stockone.connector import StockOneConnector, _extract_page
from app.connectors.providers.stockone import constants as stockone_constants
from app.connectors.providers.stockone.client import StockOneClient
from app.connectors.sync_orchestrator import sync_entity
from app.core.logging_utils import REDACTED_VALUE

@pytest.fixture
def connector_config(org, facility):
    return ConnectorConfig.objects.create(
        org=org,
        name="StockOne Failure Test",
        connector_type=ConnectorType.STOCKONE,
        facility=facility,
        config={
            "base_url": "https://stockone.example.test",
            "client_id": "client-123",
            "client_secret": "secret-456",
            "warehouse_key": "WH-001",
        },
        enabled_entities=[SyncEntityType.SKU],
    )


def _build_stockone_client(handler) -> StockOneClient:
    client = StockOneClient(
        base_url="https://stockone.example.test",
        client_id="client-123",
        client_secret="secret-456",
        warehouse_key="WH-001",
    )
    client._http.close()
    client._http = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url=client.base_url,
        timeout=client.timeout,
    )
    return client


def _build_authenticated_stockone_client(handler) -> StockOneClient:
    client = _build_stockone_client(handler)
    client._access_token = "token-123"
    client._token_expires_at = 9999999999
    return client


def _build_stockone_connector(connector_config, handler) -> StockOneConnector:
    connector = StockOneConnector(connector_config.config)
    connector._client._http.close()
    connector._client._http = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url=connector._client.base_url,
        timeout=connector._client.timeout,
    )
    return connector


def test_stockone_client_failure_captures_redacted_request_and_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == stockone_constants.AUTH_TOKEN_PATH
        return httpx.Response(
            401,
            json={
                "error": "invalid_client",
                "access_token": "should-not-leak",
            },
            request=request,
        )

    client = _build_stockone_client(handler)

    with pytest.raises(ConnectorTransportError) as exc_info:
        client.authenticate()

    details = exc_info.value.details
    assert details["operation"] == "authenticate"
    assert details["request"]["body"]["client_secret"] == REDACTED_VALUE
    assert details["response"]["status_code"] == 401
    assert details["response"]["body"]["error"] == "invalid_client"
    assert details["response"]["body"]["access_token"] == REDACTED_VALUE

    client.close()


def test_stockone_get_request_sends_no_body_and_no_content_type():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == stockone_constants.PRODUCTS_PATH
        assert request.content == b""
        assert request.headers.get("content-type") is None
        assert request.url.params.get("pagenum") == "1"
        assert request.url.params.get("page_num") is None
        assert request.url.params.get("page") is None
        return httpx.Response(
            200,
            json={"data": [], "page_info": {"current_page": 1, "total_pages": 1}},
            request=request,
        )

    client = _build_authenticated_stockone_client(handler)

    payload = client.get_products(page=1, limit=50)

    assert payload["data"] == []
    client.close()


def test_stockone_client_retries_rate_limited_request_and_succeeds(monkeypatch):
    attempts = {"count": 0}
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(
                429,
                json={"detail": "slow down"},
                request=request,
            )
        return httpx.Response(
            200,
            json={"data": [], "page_info": {"current_page": 1, "total_pages": 1}},
            request=request,
        )

    monkeypatch.setattr(
        "app.connectors.providers.stockone.client.time.sleep",
        delays.append,
    )
    client = _build_authenticated_stockone_client(handler)

    payload = client.get_products(page=1, limit=50)

    assert payload["data"] == []
    assert attempts["count"] == 2
    assert delays == [1.0]
    client.close()


def test_stockone_client_prefers_retry_after_header(monkeypatch):
    attempts = {"count": 0}
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "7"},
                json={"detail": "slow down"},
                request=request,
            )
        return httpx.Response(
            200,
            json={"data": [], "page_info": {"current_page": 1, "total_pages": 1}},
            request=request,
        )

    monkeypatch.setattr(
        "app.connectors.providers.stockone.client.time.sleep",
        delays.append,
    )
    client = _build_authenticated_stockone_client(handler)

    payload = client.get_products(page=1, limit=50)

    assert payload["data"] == []
    assert delays == [7.0]
    client.close()


def test_stockone_client_falls_back_when_retry_after_is_invalid(monkeypatch):
    attempts = {"count": 0}
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 3:
            return httpx.Response(
                429,
                headers={"Retry-After": "later"},
                json={"detail": "slow down"},
                request=request,
            )
        return httpx.Response(
            200,
            json={"data": [], "page_info": {"current_page": 1, "total_pages": 1}},
            request=request,
        )

    monkeypatch.setattr(
        "app.connectors.providers.stockone.client.time.sleep",
        delays.append,
    )
    client = _build_authenticated_stockone_client(handler)

    payload = client.get_products(page=1, limit=50)

    assert payload["data"] == []
    assert delays == [1.0, 2.0]
    client.close()


def test_stockone_client_persistent_429_includes_rate_limit_details(monkeypatch):
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == stockone_constants.AUTH_TOKEN_PATH
        return httpx.Response(
            429,
            headers={"Retry-After": "4"},
            json={
                "detail": "too many requests",
                "access_token": "should-not-leak",
            },
            request=request,
        )

    monkeypatch.setattr(
        "app.connectors.providers.stockone.client.time.sleep",
        delays.append,
    )
    client = _build_stockone_client(handler)
    client._rate_limit_max_retries = 2

    with pytest.raises(ConnectorTransportError) as exc_info:
        client.authenticate()

    details = exc_info.value.details
    assert details["request"]["body"]["client_secret"] == REDACTED_VALUE
    assert details["response"]["body"]["access_token"] == REDACTED_VALUE
    assert details["rate_limit"] == {
        "attempt_count": 3,
        "delays_seconds": [4.0, 4.0],
        "retry_after": 4.0,
        "exhausted": True,
    }
    assert delays == [4.0, 4.0]
    client.close()


def test_stockone_client_does_not_retry_non_rate_limited_failures(monkeypatch):
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500,
            json={"detail": "boom"},
            request=request,
        )

    monkeypatch.setattr(
        "app.connectors.providers.stockone.client.time.sleep",
        delays.append,
    )
    client = _build_authenticated_stockone_client(handler)

    with pytest.raises(ConnectorTransportError) as exc_info:
        client.get_products(page=1, limit=50)

    assert exc_info.value.details["response"]["status_code"] == 500
    assert delays == []
    client.close()


def test_stockone_extract_page_uses_requested_page_when_response_lags():
    records, next_page = _extract_page(
        {
            "data": [{"sku_code": "SKU-002"}],
            "page_info": {
                "current_page": 1,
                "total_pages": 4,
            },
        },
        requested_page=2,
    )

    assert records == [{"sku_code": "SKU-002"}]
    assert next_page == 3


@pytest.mark.django_db
def test_sync_entity_updates_progress_after_each_api_page(connector_config):
    sync_log = SyncLog.objects.create(
        connector=connector_config,
        org=connector_config.org,
        entity_type=SyncEntityType.CUSTOMER,
        status=SyncStatus.PENDING,
    )
    checkpoints: list[dict[str, object]] = []

    class PagingConnector:
        def __init__(self) -> None:
            self.calls = 0

        def fetch_customers(self, cursor=None):
            self.calls += 1
            if self.calls == 1:
                assert cursor is None
                return [
                    {
                        "customer_reference": "CUST-001",
                        "name": "First Customer",
                    }
                ], 2

            assert cursor == 2
            sync_log.refresh_from_db()
            checkpoints.append(
                {
                    "status": sync_log.status,
                    "records_fetched": sync_log.records_fetched,
                    "records_created": sync_log.records_created,
                    "records_failed": sync_log.records_failed,
                    "cursor_state": sync_log.cursor_state,
                    "mapping_count": ExternalEntityMapping.objects.filter(
                        connector=connector_config,
                        entity_type=SyncEntityType.CUSTOMER,
                    ).count(),
                }
            )
            return [
                {
                    "customer_reference": "CUST-002",
                    "name": "Second Customer",
                }
            ], None

        def fetch_products(self, cursor=None):
            return [], None

        def fetch_inventory(self, cursor=None):
            return [], None

        def fetch_orders(self, cursor=None, since=None):
            return [], None

        def fetch_purchase_orders(self, cursor=None, since=None):
            return [], None

        def fetch_suppliers(self, cursor=None):
            return [], None

    log = sync_entity(
        connector_config,
        SyncEntityType.CUSTOMER,
        PagingConnector(),
        sync_log=sync_log,
    )

    assert checkpoints == [
        {
            "status": SyncStatus.RUNNING,
            "records_fetched": 1,
            "records_created": 1,
            "records_failed": 0,
            "cursor_state": {
                "requested_cursor": 1,
                "next_cursor": 2,
                "pages_completed": 1,
                "page_record_count": 1,
            },
            "mapping_count": 1,
        }
    ]
    assert log.status == SyncStatus.COMPLETED
    assert log.records_fetched == 2
    assert log.records_created == 2
    assert log.cursor_state == {
        "requested_cursor": 2,
        "next_cursor": None,
        "pages_completed": 2,
        "page_record_count": 1,
    }


@pytest.mark.django_db
def test_sync_entity_persists_upstream_failure_details(connector_config):
    class FailingConnector:
        def fetch_products(self, cursor=None):
            raise ConnectorTransportError(
                "StockOne request failed during get_products.",
                details={
                    "connector_type": "STOCKONE",
                    "operation": "get_products",
                    "request": {
                        "method": "GET",
                        "url": "https://stockone.example.test/api/products?page=1",
                    },
                    "response": {
                        "status_code": 500,
                        "body": {"message": "upstream exploded"},
                    },
                    "error": "Server error '500 Internal Server Error'",
                },
            )

        def fetch_inventory(self, cursor=None):
            return [], None

        def fetch_orders(self, cursor=None, since=None):
            return [], None

        def fetch_purchase_orders(self, cursor=None, since=None):
            return [], None

        def fetch_suppliers(self, cursor=None):
            return [], None

        def fetch_customers(self, cursor=None):
            return [], None

    log = sync_entity(
        connector_config,
        SyncEntityType.SKU,
        FailingConnector(),
    )

    assert log.status == SyncStatus.FAILED
    assert log.error_details is not None
    assert log.error_details[0]["type"] == "fatal"
    assert log.error_details[0]["details"]["operation"] == "get_products"
    assert log.error_details[0]["details"]["response"]["status_code"] == 500


@pytest.mark.django_db
def test_sync_entity_completes_after_transient_rate_limit(
    connector_config,
    monkeypatch,
):
    product_attempts = {"count": 0}
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == stockone_constants.AUTH_TOKEN_PATH:
            return httpx.Response(
                200,
                json={
                    "access_token": "token-123",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
                request=request,
            )

        if request.url.path == stockone_constants.PRODUCTS_PATH:
            product_attempts["count"] += 1
            if product_attempts["count"] == 1:
                return httpx.Response(
                    429,
                    json={"detail": "slow down"},
                    request=request,
                )
            return httpx.Response(
                200,
                json={"data": [], "page_info": {"current_page": 1, "total_pages": 1}},
                request=request,
            )

        raise AssertionError(f"Unexpected path: {request.url.path}")

    monkeypatch.setattr(
        "app.connectors.providers.stockone.client.time.sleep",
        delays.append,
    )
    connector = _build_stockone_connector(connector_config, handler)

    log = sync_entity(
        connector_config,
        SyncEntityType.SKU,
        connector,
    )

    assert log.status == SyncStatus.COMPLETED
    assert log.error_details is None
    assert log.records_fetched == 0
    assert delays == [1.0]
    connector.close()


@pytest.mark.django_db
def test_sync_entity_persists_rate_limit_failure_details(
    connector_config,
    monkeypatch,
):
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == stockone_constants.AUTH_TOKEN_PATH:
            return httpx.Response(
                200,
                json={
                    "access_token": "token-123",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
                request=request,
            )

        if request.url.path == stockone_constants.PRODUCTS_PATH:
            return httpx.Response(
                429,
                headers={"Retry-After": "3"},
                json={
                    "detail": "too many requests",
                    "access_token": "should-not-leak",
                },
                request=request,
            )

        raise AssertionError(f"Unexpected path: {request.url.path}")

    monkeypatch.setattr(
        "app.connectors.providers.stockone.client.time.sleep",
        delays.append,
    )
    connector = _build_stockone_connector(connector_config, handler)
    connector._client._rate_limit_max_retries = 2

    log = sync_entity(
        connector_config,
        SyncEntityType.SKU,
        connector,
    )

    assert log.status == SyncStatus.FAILED
    assert log.error_details is not None
    assert log.error_details[0]["type"] == "fatal"
    assert log.error_details[0]["details"]["response"]["body"]["access_token"] == (
        REDACTED_VALUE
    )
    assert log.error_details[0]["details"]["rate_limit"] == {
        "attempt_count": 3,
        "delays_seconds": [3.0, 3.0],
        "retry_after": 3.0,
        "exhausted": True,
    }
    assert delays == [3.0, 3.0]
    connector.close()
