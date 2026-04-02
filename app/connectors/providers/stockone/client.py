"""Low-level HTTP client for the StockOne Neo API.

Handles OAuth2 token lifecycle and exposes thin wrappers around every
endpoint the connector needs.  All methods are synchronous (httpx).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from app.connectors.exceptions import ConnectorTransportError
from app.connectors.providers.stockone import constants as C
from app.core.config import get_runtime_settings
from app.core.logging_utils import log_event, redact_sensitive, sanitize_for_log

logger = logging.getLogger("wms.connectors.stockone")

TOKEN_REFRESH_MARGIN_SECONDS = 300  # refresh 5 min before expiry
STOCKONE_PAGE_PARAM = "pagenum"


class StockOneClient:

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        warehouse_key: str,
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.warehouse_key = warehouse_key
        self.timeout = timeout
        runtime_settings = get_runtime_settings()

        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._rate_limit_max_retries = runtime_settings.connector_rate_limit_max_retries
        self._rate_limit_initial_delay_seconds = (
            runtime_settings.connector_rate_limit_initial_delay_seconds
        )
        self._rate_limit_max_delay_seconds = (
            runtime_settings.connector_rate_limit_max_delay_seconds
        )

        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def close(self) -> None:
        self._http.close()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> dict[str, Any]:
        """Obtain a fresh access token via OAuth2 client_credentials."""
        data = self._request_json(
            "POST",
            C.AUTH_TOKEN_PATH,
            operation="authenticate",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
        )
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 36000)
        logger.info("StockOne token acquired, expires_in=%s", data.get("expires_in"))
        return data

    def _ensure_token(self) -> None:
        if (
            self._access_token is None
            or time.time() >= self._token_expires_at - TOKEN_REFRESH_MARGIN_SECONDS
        ):
            self.authenticate()

    def _headers(self, *, include_content_type: bool = True) -> dict[str, str]:
        self._ensure_token()
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "warehouse": self.warehouse_key,
        }
        if include_content_type:
            headers["Content-Type"] = "application/json"
        return headers

    # ------------------------------------------------------------------
    # Generic request helpers
    # ------------------------------------------------------------------

    def _decode_response_body(self, response: httpx.Response | None) -> Any:
        if response is None or not response.content:
            return None

        content_type = response.headers.get("Content-Type", "")
        decoded = response.content.decode("utf-8", errors="replace")
        if content_type and "json" in content_type.lower():
            try:
                return json.loads(decoded)
            except json.JSONDecodeError:
                return decoded

        try:
            return json.loads(decoded)
        except json.JSONDecodeError:
            return decoded

    def _capture_request(
        self,
        request: httpx.Request,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
    ) -> dict[str, Any]:
        return redact_sensitive(
            {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "params": sanitize_for_log(params),
                "body": sanitize_for_log(body),
            }
        )

    def _capture_response(self, response: httpx.Response | None) -> dict[str, Any] | None:
        if response is None:
            return None
        return redact_sensitive(
            {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": sanitize_for_log(self._decode_response_body(response)),
            }
        )

    def _raise_request_error(
        self,
        exc: Exception,
        *,
        operation: str,
        request_snapshot: dict[str, Any],
        response: httpx.Response | None = None,
        extra_details: dict[str, Any] | None = None,
    ) -> None:
        response_snapshot = self._capture_response(response)
        details = {
            "connector_type": "STOCKONE",
            "operation": operation,
            "request": request_snapshot,
            "response": response_snapshot,
            "error": str(exc),
        }
        if extra_details:
            details.update(sanitize_for_log(extra_details))
        log_event(
            logger,
            logging.ERROR,
            "connector.http.failure",
            connector_type="STOCKONE",
            operation=operation,
            request=request_snapshot,
            response=response_snapshot,
            error=str(exc),
            **sanitize_for_log(extra_details or {}),
        )
        raise ConnectorTransportError(
            f"StockOne request failed during {operation}.",
            details=details,
        ) from exc

    def _parse_retry_after(self, retry_after: str | None) -> float | None:
        if retry_after is None:
            return None

        value = retry_after.strip()
        if not value:
            return None

        try:
            return max(0.0, float(value))
        except ValueError:
            pass

        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError, OverflowError):
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return max(
            0.0,
            (parsed - datetime.now(timezone.utc)).total_seconds(),
        )

    def _resolve_rate_limit_delay(
        self,
        retry_attempt: int,
        retry_after_header: str | None,
    ) -> tuple[float, bool, float | None]:
        parsed_retry_after = self._parse_retry_after(retry_after_header)
        if parsed_retry_after is not None:
            return (
                min(parsed_retry_after, float(self._rate_limit_max_delay_seconds)),
                True,
                parsed_retry_after,
            )

        fallback_delay = float(
            self._rate_limit_initial_delay_seconds * (2 ** (retry_attempt - 1))
        )
        return (
            min(fallback_delay, float(self._rate_limit_max_delay_seconds)),
            False,
            None,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        operation: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json_body: Any = None,
    ) -> httpx.Response:
        request_kwargs: dict[str, Any] = {
            "headers": headers,
            "params": params,
        }
        if method.upper() not in {"GET", "HEAD"}:
            if data is not None:
                request_kwargs["data"] = data
            if json_body is not None:
                request_kwargs["json"] = json_body

        def _build_request() -> httpx.Request:
            return self._http.build_request(method, path, **request_kwargs)

        request = _build_request()
        request_snapshot = self._capture_request(
            request,
            params=params,
            body=json_body if json_body is not None else data,
        )
        rate_limit_delays: list[float] = []

        for retry_attempt in range(self._rate_limit_max_retries + 1):
            request = _build_request()

            try:
                response = self._http.send(request)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code != 429:
                    self._raise_request_error(
                        exc,
                        operation=operation,
                        request_snapshot=request_snapshot,
                        response=exc.response,
                    )

                retry_after_header = exc.response.headers.get("Retry-After")
                parsed_retry_after = self._parse_retry_after(retry_after_header)

                if retry_attempt >= self._rate_limit_max_retries:
                    self._raise_request_error(
                        exc,
                        operation=operation,
                        request_snapshot=request_snapshot,
                        response=exc.response,
                        extra_details={
                            "rate_limit": {
                                "attempt_count": len(rate_limit_delays) + 1,
                                "delays_seconds": rate_limit_delays,
                                "retry_after": parsed_retry_after,
                                "exhausted": True,
                            }
                        },
                    )

                delay_seconds, used_retry_after, parsed_retry_after = (
                    self._resolve_rate_limit_delay(
                        retry_attempt + 1,
                        retry_after_header,
                    )
                )
                rate_limit_delays.append(delay_seconds)

                log_event(
                    logger,
                    logging.WARNING,
                    "connector.http.rate_limited",
                    connector_type="STOCKONE",
                    operation=operation,
                    attempt=retry_attempt + 1,
                    max_retries=self._rate_limit_max_retries,
                    delay_seconds=delay_seconds,
                    used_retry_after=used_retry_after,
                    retry_after=parsed_retry_after,
                )
                time.sleep(delay_seconds)
            except httpx.RequestError as exc:
                self._raise_request_error(
                    exc,
                    operation=operation,
                    request_snapshot=request_snapshot,
                )

        raise AssertionError("Rate-limit retry loop exited unexpectedly.")

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        operation: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json_body: Any = None,
    ) -> dict[str, Any]:
        response = self._request(
            method,
            path,
            operation=operation,
            headers=headers,
            params=params,
            data=data,
            json_body=json_body,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            self._raise_request_error(
                exc,
                operation=operation,
                request_snapshot=self._capture_request(
                    response.request,
                    params=params,
                    body=json_body if json_body is not None else data,
                ),
                response=response,
            )

        if not isinstance(payload, dict):
            self._raise_request_error(
                ValueError("Expected JSON object response."),
                operation=operation,
                request_snapshot=self._capture_request(
                    response.request,
                    params=params,
                    body=json_body if json_body is not None else data,
                ),
                response=response,
            )

        return payload

    def _get(
        self,
        path: str,
        *,
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request_json(
            "GET",
            path,
            operation=operation,
            headers=self._headers(include_content_type=False),
            params=params,
        )

    def _get_paginated(
        self,
        path: str,
        *,
        operation: str,
        page: int = 1,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = dict(params or {})
        params[STOCKONE_PAGE_PARAM] = page
        return self._get(path, operation=operation, params=params)

    # ------------------------------------------------------------------
    # Products (SKU)
    # ------------------------------------------------------------------

    def get_products(
        self,
        page: int = 1,
        limit: int = C.DEFAULT_PAGE_SIZE,
        sku_code: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if sku_code:
            params["sku_code"] = sku_code
        return self._get_paginated(
            C.PRODUCTS_PATH,
            operation="get_products",
            page=page,
            params=params,
        )

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------

    def get_inventory(
        self,
        page: int = 1,
        sku_code: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if sku_code:
            params["sku_code"] = sku_code
        return self._get_paginated(
            C.INVENTORY_PATH,
            operation="get_inventory",
            page=page,
            params=params,
        )

    def get_move_inventory(
        self,
        page: int = 1,
        sku_code: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if sku_code:
            params["sku_code"] = sku_code
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        return self._get_paginated(
            C.MOVE_INVENTORY_PATH,
            operation="get_move_inventory",
            page=page,
            params=params,
        )

    # ------------------------------------------------------------------
    # Orders (outbound)
    # ------------------------------------------------------------------

    def get_orders(
        self,
        page: int = 1,
        order_reference: str | None = None,
        order_type: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if order_reference:
            params["order_reference"] = order_reference
        if order_type:
            params["order_type"] = order_type
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        return self._get_paginated(
            C.ORDERS_V1_PATH,
            operation="get_orders",
            page=page,
            params=params,
        )

    # ------------------------------------------------------------------
    # Purchase Orders (inbound)
    # ------------------------------------------------------------------

    def get_purchase_orders(
        self,
        page: int = 1,
        po_reference: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if po_reference:
            params["po_reference"] = po_reference
        return self._get_paginated(
            C.PURCHASE_ORDER_PATH,
            operation="get_purchase_orders",
            page=page,
            params=params,
        )

    # ------------------------------------------------------------------
    # Suppliers
    # ------------------------------------------------------------------

    def get_suppliers(
        self,
        page: int = 1,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        return self._get_paginated(
            C.SUPPLIER_PATH,
            operation="get_suppliers",
            page=page,
            params=params,
        )

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    def get_customers(self, page: int = 1) -> dict[str, Any]:
        # StockOne customer list is not a documented GET endpoint in Neo;
        # this is a placeholder that returns empty if unavailable.
        try:
            return self._get_paginated(
                C.CUSTOMER_PATH,
                operation="get_customers",
                page=page,
            )
        except ConnectorTransportError:
            return {"data": [], "page_info": {"current_page": 1, "total_pages": 1}}

    # ------------------------------------------------------------------
    # Invoices
    # ------------------------------------------------------------------

    def get_invoices(self, page: int = 1) -> dict[str, Any]:
        return self._get_paginated(
            C.INVOICE_PATH,
            operation="get_invoices",
            page=page,
        )

    # ------------------------------------------------------------------
    # Picklist
    # ------------------------------------------------------------------

    def get_picklists(self, page: int = 1) -> dict[str, Any]:
        return self._get_paginated(
            C.PICKLIST_PATH,
            operation="get_picklists",
            page=page,
        )
