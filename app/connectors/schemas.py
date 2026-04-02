from __future__ import annotations

from typing import Any
from uuid import UUID

from ninja import Schema


# ------------------------------------------------------------------
# ConnectorConfig
# ------------------------------------------------------------------

class ConnectorConfigCreateIn(Schema):
    name: str
    connector_type: str
    config: dict[str, Any]
    facility_id: UUID | None = None
    sync_interval_minutes: int = 60
    enabled_entities: list[str] = []


class ConnectorConfigUpdateIn(Schema):
    name: str | None = None
    is_active: bool | None = None
    config: dict[str, Any] | None = None
    facility_id: UUID | None = None
    sync_interval_minutes: int | None = None
    enabled_entities: list[str] | None = None


class ConnectorConfigOut(Schema):
    id: UUID
    name: str
    connector_type: str
    is_active: bool
    facility_id: UUID | None = None
    config: dict[str, Any]
    sync_interval_minutes: int
    enabled_entities: list[str]
    last_synced_at: str | None = None
    created_at: str
    updated_at: str


# ------------------------------------------------------------------
# Sync
# ------------------------------------------------------------------

class SyncTriggerIn(Schema):
    entity_types: list[str] | None = None


class SyncLogOut(Schema):
    id: UUID
    connector_id: UUID
    entity_type: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    records_fetched: int
    records_created: int
    records_updated: int
    records_skipped: int
    records_failed: int
    error_details: Any | None = None
    created_at: str


# ------------------------------------------------------------------
# Test connection
# ------------------------------------------------------------------

class TestConnectionOut(Schema):
    status: str
    token_type: str | None = None
    expires_in: int | None = None
    scope: str | None = None
