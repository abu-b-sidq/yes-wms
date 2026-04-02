"""Sync orchestrator — coordinates pulling data from an external connector
and upserting it into YES WMS via the existing service layer.

Handles pagination, SHA-256 change detection, create/update routing,
and per-record error capture.
"""

from __future__ import annotations

import hashlib
import json
import logging
from decimal import Decimal
from typing import Any, Callable

from django.utils import timezone

from app.connectors.base_connector import BaseConnector
from app.connectors.enums import ConnectorType, SyncEntityType, SyncStatus
from app.connectors.models import ConnectorConfig, ExternalEntityMapping, SyncLog
from app.connectors.providers.stockone.connector import StockOneConnector
from app.connectors.providers.stockone import mapper as stockone_mapper
from app.core.exceptions import EntityNotFoundError, ValidationError
from app.core.logging_utils import sanitize_for_log
from app.inventory.models import InventoryBalance
from app.masters.models import Facility, Organization, SKU
from app.masters import services as masters_svc

logger = logging.getLogger("wms.connectors.orchestrator")

# Sync order matters: SKUs must exist before inventory/orders reference them.
SYNC_ORDER = [
    SyncEntityType.SUPPLIER,
    SyncEntityType.CUSTOMER,
    SyncEntityType.SKU,
    SyncEntityType.INVENTORY,
    SyncEntityType.PURCHASE_ORDER,
    SyncEntityType.ORDER,
]


def _hash_record(record: dict) -> str:
    raw = json.dumps(record, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _build_cursor_state(
    *,
    requested_cursor: Any,
    next_cursor: Any,
    pages_completed: int,
    page_record_count: int,
) -> dict[str, Any]:
    return {
        "requested_cursor": requested_cursor,
        "next_cursor": next_cursor,
        "pages_completed": pages_completed,
        "page_record_count": page_record_count,
    }


def _save_sync_progress(
    sync_log: SyncLog,
    *,
    status: str,
    records_fetched: int,
    records_created: int,
    records_updated: int,
    records_skipped: int,
    records_failed: int,
    cursor_state: dict[str, Any] | None,
    error_details: list[dict[str, Any]] | None = None,
    completed_at=None,
) -> None:
    sync_log.status = status
    sync_log.records_fetched = records_fetched
    sync_log.records_created = records_created
    sync_log.records_updated = records_updated
    sync_log.records_skipped = records_skipped
    sync_log.records_failed = records_failed
    sync_log.cursor_state = cursor_state
    sync_log.error_details = error_details
    sync_log.completed_at = completed_at
    sync_log.save(
        update_fields=[
            "status",
            "records_fetched",
            "records_created",
            "records_updated",
            "records_skipped",
            "records_failed",
            "cursor_state",
            "error_details",
            "completed_at",
            "updated_at",
        ]
    )


def _get_connector_instance(config: ConnectorConfig) -> BaseConnector:
    if config.connector_type == ConnectorType.STOCKONE:
        return StockOneConnector(config.config)
    raise ValueError(f"Unsupported connector type: {config.connector_type}")


def _get_fetch_method(
    connector: BaseConnector, entity_type: str,
) -> Callable:
    mapping = {
        SyncEntityType.SKU: connector.fetch_products,
        SyncEntityType.INVENTORY: connector.fetch_inventory,
        SyncEntityType.ORDER: connector.fetch_orders,
        SyncEntityType.PURCHASE_ORDER: connector.fetch_purchase_orders,
        SyncEntityType.SUPPLIER: connector.fetch_suppliers,
        SyncEntityType.CUSTOMER: connector.fetch_customers,
    }
    method = mapping.get(entity_type)
    if method is None:
        raise ValueError(f"No fetch method for entity type: {entity_type}")
    return method


def _get_mapper_and_id_fn(
    connector_type: str, entity_type: str,
) -> tuple[Callable, Callable]:
    """Return (map_fn, external_id_fn) for a given connector+entity combo."""
    if connector_type == ConnectorType.STOCKONE:
        mapping = {
            SyncEntityType.SKU: (
                stockone_mapper.map_product_to_sku,
                stockone_mapper.get_product_external_id,
            ),
            SyncEntityType.INVENTORY: (
                stockone_mapper.map_inventory_to_balance,
                stockone_mapper.get_inventory_external_id,
            ),
            SyncEntityType.ORDER: (
                stockone_mapper.map_order_to_transaction,
                stockone_mapper.get_order_external_id,
            ),
            SyncEntityType.PURCHASE_ORDER: (
                stockone_mapper.map_purchase_order_to_transaction,
                stockone_mapper.get_purchase_order_external_id,
            ),
            SyncEntityType.SUPPLIER: (
                stockone_mapper.map_supplier,
                stockone_mapper.get_supplier_external_id,
            ),
            SyncEntityType.CUSTOMER: (
                stockone_mapper.map_customer,
                stockone_mapper.get_customer_external_id,
            ),
        }
        result = mapping.get(entity_type)
        if result is None:
            raise ValueError(
                f"No mapper for {connector_type}/{entity_type}"
            )
        return result
    raise ValueError(f"Unsupported connector type: {connector_type}")


# ------------------------------------------------------------------
# Per-entity upsert logic
# ------------------------------------------------------------------

def _upsert_sku(
    org: Organization, mapped: dict[str, Any], existing_id: str | None,
) -> str:
    """Create or update a SKU.  Returns the internal UUID as str."""
    code = mapped["code"]
    if existing_id:
        sku = masters_svc.update_sku(org, code, mapped, user="connector-sync")
    else:
        sku = masters_svc.create_sku(org, mapped, user="connector-sync")
    return str(sku.id)


def _upsert_inventory(
    org: Organization,
    facility: Facility | None,
    mapped: dict[str, Any],
    existing_id: str | None,
) -> str:
    """Upsert an InventoryBalance row.  Returns the internal UUID as str."""
    sku_code = mapped["sku_code"]
    try:
        sku = SKU.objects.get(org=org, code=sku_code)
    except SKU.DoesNotExist:
        raise EntityNotFoundError(
            f"SKU '{sku_code}' not found — sync SKUs first."
        )

    if facility is None:
        facility = Facility.objects.filter(org=org, is_active=True).first()
        if facility is None:
            raise ValidationError("No active facility found for inventory sync.")

    balance, _created = InventoryBalance.objects.update_or_create(
        org=org,
        facility=facility,
        sku=sku,
        entity_type="LOCATION",
        entity_code="STOCKONE_SYNC",
        batch_number="",
        defaults={
            "quantity_on_hand": mapped["quantity_on_hand"],
            "quantity_reserved": mapped["quantity_reserved"],
            "quantity_available": mapped["quantity_available"],
        },
    )
    return str(balance.id)


def _upsert_reference(
    org: Organization, mapped: dict[str, Any], existing_id: str | None,
) -> str:
    """Store suppliers/customers as reference data in the mapping table.
    Returns a stable pseudo-ID derived from the external id."""
    import uuid
    if existing_id:
        return existing_id
    return str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(mapped, sort_keys=True, default=str)))


# ------------------------------------------------------------------
# Orchestration
# ------------------------------------------------------------------

def sync_entity(
    config: ConnectorConfig,
    entity_type: str,
    connector: BaseConnector,
    sync_log: SyncLog | None = None,
) -> SyncLog:
    """Run a full sync for a single entity type on a connector config."""
    org = config.org
    facility = config.facility

    if sync_log is None:
        sync_log = SyncLog.objects.create(
            connector=config,
            org=org,
            entity_type=entity_type,
            status=SyncStatus.RUNNING,
            started_at=timezone.now(),
        )
    else:
        sync_log.status = SyncStatus.RUNNING
        sync_log.started_at = timezone.now()
        sync_log.completed_at = None
        sync_log.records_fetched = 0
        sync_log.records_created = 0
        sync_log.records_updated = 0
        sync_log.records_skipped = 0
        sync_log.records_failed = 0
        sync_log.error_details = None
        sync_log.cursor_state = None
        sync_log.save()

    map_fn, id_fn = _get_mapper_and_id_fn(config.connector_type, entity_type)
    fetch_fn = _get_fetch_method(connector, entity_type)
    errors: list[dict] = []

    cursor = None
    total_fetched = 0
    total_created = 0
    total_updated = 0
    total_skipped = 0
    total_failed = 0
    pages_completed = 0
    last_requested_cursor = None
    last_next_cursor = None
    last_page_record_count = 0

    def _error_entry(exc: Exception, *, external_id: str | None = None, error_type: str = "record") -> dict[str, Any]:
        entry: dict[str, Any] = {
            "error": str(exc),
            "type": error_type,
        }
        if external_id is not None:
            entry["external_id"] = external_id

        details = getattr(exc, "details", None)
        if details is not None:
            entry["details"] = sanitize_for_log(details)
        return entry

    try:
        while True:
            requested_cursor = cursor or 1
            records, next_cursor = fetch_fn(cursor=cursor)
            total_fetched += len(records)
            last_requested_cursor = requested_cursor
            last_next_cursor = next_cursor
            last_page_record_count = len(records)

            for record in records:
                try:
                    external_id = id_fn(record)
                    if not external_id:
                        total_skipped += 1
                        continue

                    record_hash = _hash_record(record)

                    existing = ExternalEntityMapping.objects.filter(
                        connector=config,
                        entity_type=entity_type,
                        external_id=external_id,
                    ).first()

                    if existing and existing.external_hash == record_hash:
                        total_skipped += 1
                        continue

                    mapped = map_fn(record)

                    # Route to the correct upsert handler
                    if entity_type == SyncEntityType.SKU:
                        internal_id = _upsert_sku(
                            org, mapped, str(existing.internal_id) if existing else None,
                        )
                    elif entity_type == SyncEntityType.INVENTORY:
                        internal_id = _upsert_inventory(
                            org, facility, mapped, str(existing.internal_id) if existing else None,
                        )
                    elif entity_type in (SyncEntityType.SUPPLIER, SyncEntityType.CUSTOMER):
                        internal_id = _upsert_reference(
                            org, mapped, str(existing.internal_id) if existing else None,
                        )
                    elif entity_type in (SyncEntityType.ORDER, SyncEntityType.PURCHASE_ORDER):
                        # Orders/POs are stored as reference mappings for now;
                        # full transaction creation requires deeper integration
                        # with the operations service and is phase-2 work.
                        internal_id = _upsert_reference(
                            org, mapped, str(existing.internal_id) if existing else None,
                        )
                    else:
                        total_skipped += 1
                        continue

                    if existing:
                        existing.external_hash = record_hash
                        existing.internal_id = internal_id
                        existing.save(update_fields=["external_hash", "internal_id", "updated_at"])
                        total_updated += 1
                    else:
                        ExternalEntityMapping.objects.create(
                            org=org,
                            connector=config,
                            entity_type=entity_type,
                            external_id=external_id,
                            internal_id=internal_id,
                            external_hash=record_hash,
                        )
                        total_created += 1

                except Exception as exc:
                    total_failed += 1
                    errors.append(
                        _error_entry(
                            exc,
                            external_id=id_fn(record) if record else "unknown",
                        )
                    )
                    logger.warning(
                        "Sync record error: connector=%s entity=%s error=%s",
                        config.name, entity_type, exc,
                    )

            pages_completed += 1
            _save_sync_progress(
                sync_log,
                status=SyncStatus.RUNNING,
                records_fetched=total_fetched,
                records_created=total_created,
                records_updated=total_updated,
                records_skipped=total_skipped,
                records_failed=total_failed,
                cursor_state=_build_cursor_state(
                    requested_cursor=requested_cursor,
                    next_cursor=next_cursor,
                    pages_completed=pages_completed,
                    page_record_count=len(records),
                ),
                error_details=errors or None,
            )

            if next_cursor is None:
                break
            cursor = next_cursor

        sync_log.status = SyncStatus.COMPLETED if total_failed == 0 else SyncStatus.COMPLETED
        if total_failed > 0 and total_created == 0 and total_updated == 0:
            sync_log.status = SyncStatus.FAILED

    except Exception as exc:
        sync_log.status = SyncStatus.FAILED
        errors.append(_error_entry(exc, error_type="fatal"))
        logger.exception("Sync failed: connector=%s entity=%s", config.name, entity_type)

    _save_sync_progress(
        sync_log,
        status=sync_log.status,
        records_fetched=total_fetched,
        records_created=total_created,
        records_updated=total_updated,
        records_skipped=total_skipped,
        records_failed=total_failed,
        cursor_state=(
            _build_cursor_state(
                requested_cursor=last_requested_cursor,
                next_cursor=last_next_cursor,
                pages_completed=pages_completed,
                page_record_count=last_page_record_count,
            )
            if pages_completed > 0
            else None
        ),
        error_details=errors or None,
        completed_at=timezone.now(),
    )

    return sync_log


def run_sync(
    config: ConnectorConfig,
    entity_types: list[str] | None = None,
    sync_logs_by_entity: dict[str, SyncLog] | None = None,
) -> list[SyncLog]:
    """Run a full sync cycle for a connector, respecting sync order."""
    enabled = set(config.enabled_entities or [])
    if entity_types:
        enabled = enabled & set(entity_types)

    ordered = [et for et in SYNC_ORDER if et in enabled]

    connector = _get_connector_instance(config)
    logs: list[SyncLog] = []

    try:
        connector.authenticate()

        for entity_type in ordered:
            logger.info(
                "Syncing %s for connector %s (org=%s)",
                entity_type, config.name, config.org_id,
            )
            log = sync_entity(
                config,
                entity_type,
                connector,
                sync_log=(sync_logs_by_entity or {}).get(entity_type),
            )
            logs.append(log)

        config.last_synced_at = timezone.now()
        config.save(update_fields=["last_synced_at", "updated_at"])

    finally:
        if hasattr(connector, "close"):
            connector.close()

    return logs
