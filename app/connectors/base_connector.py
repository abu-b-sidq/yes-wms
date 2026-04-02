from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Abstract base class for all external WMS connectors.

    Each connector implementation wraps a specific external API and exposes
    a uniform interface that the sync orchestrator consumes.  Every fetch
    method returns ``(records, next_cursor)`` where *records* is a list of
    raw dicts (vendor-specific) and *next_cursor* is an opaque value the
    orchestrator passes back on the next call (``None`` when exhausted).
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    def authenticate(self) -> None:
        """Obtain / refresh credentials for the external system."""

    @abstractmethod
    def test_connection(self) -> dict[str, Any]:
        """Verify connectivity.  Return a status dict on success, raise on failure."""

    # ------------------------------------------------------------------
    # Data fetching — each returns (list[dict], next_cursor | None)
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch_products(
        self, cursor: Any | None = None,
    ) -> tuple[list[dict], Any | None]:
        """Fetch product / SKU master data."""

    @abstractmethod
    def fetch_inventory(
        self, cursor: Any | None = None,
    ) -> tuple[list[dict], Any | None]:
        """Fetch current inventory balances."""

    @abstractmethod
    def fetch_orders(
        self, cursor: Any | None = None, since: str | None = None,
    ) -> tuple[list[dict], Any | None]:
        """Fetch outbound orders."""

    @abstractmethod
    def fetch_purchase_orders(
        self, cursor: Any | None = None, since: str | None = None,
    ) -> tuple[list[dict], Any | None]:
        """Fetch inbound purchase orders."""

    @abstractmethod
    def fetch_suppliers(
        self, cursor: Any | None = None,
    ) -> tuple[list[dict], Any | None]:
        """Fetch supplier master data."""

    @abstractmethod
    def fetch_customers(
        self, cursor: Any | None = None,
    ) -> tuple[list[dict], Any | None]:
        """Fetch customer master data."""
