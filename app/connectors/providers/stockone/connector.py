"""StockOne connector — implements BaseConnector using StockOneClient."""

from __future__ import annotations

import logging
from typing import Any

from app.connectors.base_connector import BaseConnector
from app.connectors.providers.stockone.client import StockOneClient

logger = logging.getLogger("wms.connectors.stockone")


def _coerce_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _extract_page(
    response: dict[str, Any],
    *,
    requested_page: int,
) -> tuple[list[dict], int | None]:
    """Return (records, next_page_or_None) from a StockOne paginated response."""
    data = response.get("data", [])
    if not isinstance(data, list):
        data = [data] if data else []

    page_info = response.get("page_info")
    if isinstance(page_info, dict):
        current = _coerce_positive_int(page_info.get("current_page"), requested_page)
        total = _coerce_positive_int(page_info.get("total_pages"), current)
        effective_current = max(current, requested_page)
        next_page = effective_current + 1 if effective_current < total else None
    else:
        next_page = None
    return data, next_page


class StockOneConnector(BaseConnector):

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._client = StockOneClient(
            base_url=config["base_url"],
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            warehouse_key=config["warehouse_key"],
            timeout=config.get("timeout", 30),
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def authenticate(self) -> None:
        self._client.authenticate()

    def test_connection(self) -> dict[str, Any]:
        token_data = self._client.authenticate()
        return {
            "status": "ok",
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in"),
            "scope": token_data.get("scope"),
        }

    def close(self) -> None:
        self._client.close()

    # ------------------------------------------------------------------
    # Fetch methods — return (records, next_cursor | None)
    # ------------------------------------------------------------------

    def fetch_products(
        self, cursor: Any | None = None,
    ) -> tuple[list[dict], Any | None]:
        page = cursor or 1
        resp = self._client.get_products(page=page, limit=50)
        return _extract_page(resp, requested_page=page)

    def fetch_inventory(
        self, cursor: Any | None = None,
    ) -> tuple[list[dict], Any | None]:
        page = cursor or 1
        resp = self._client.get_inventory(page=page)
        return _extract_page(resp, requested_page=page)

    def fetch_orders(
        self, cursor: Any | None = None, since: str | None = None,
    ) -> tuple[list[dict], Any | None]:
        page = cursor or 1
        resp = self._client.get_orders(page=page, from_date=since)
        return _extract_page(resp, requested_page=page)

    def fetch_purchase_orders(
        self, cursor: Any | None = None, since: str | None = None,
    ) -> tuple[list[dict], Any | None]:
        page = cursor or 1
        resp = self._client.get_purchase_orders(page=page)
        return _extract_page(resp, requested_page=page)

    def fetch_suppliers(
        self, cursor: Any | None = None,
    ) -> tuple[list[dict], Any | None]:
        page = cursor or 1
        resp = self._client.get_suppliers(page=page)
        return _extract_page(resp, requested_page=page)

    def fetch_customers(
        self, cursor: Any | None = None,
    ) -> tuple[list[dict], Any | None]:
        page = cursor or 1
        resp = self._client.get_customers(page=page)
        return _extract_page(resp, requested_page=page)
