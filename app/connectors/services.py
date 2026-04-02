"""CRUD services for ConnectorConfig and SyncLog."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from app.connectors.enums import ConnectorType, SyncEntityType, SyncStatus
from app.connectors.models import ConnectorConfig, SyncLog
from app.connectors.sync_orchestrator import SYNC_ORDER, run_sync
from app.core.exceptions import (
    EntityNotFoundError,
    ServiceUnavailableError,
    ValidationError,
)
from app.core.logging_utils import sanitize_for_log
from app.masters.models import Organization

logger = logging.getLogger("app.connectors.services")


@dataclass(frozen=True)
class QueuedSync:
    logs: list[SyncLog]
    task_id: str


def _normalize_entity_types(
    config: ConnectorConfig,
    entity_types: list[str] | None = None,
) -> list[str]:
    valid_entities = set(SyncEntityType.values)
    enabled_entities = set(config.enabled_entities or [])
    requested_entities = set(entity_types or config.enabled_entities or [])

    invalid_entities = sorted(requested_entities - valid_entities)
    if invalid_entities:
        raise ValidationError(
            "Unsupported entity types requested for sync.",
            details={"entity_types": invalid_entities},
        )

    ordered_entities = [
        entity_type
        for entity_type in SYNC_ORDER
        if entity_type in enabled_entities and entity_type in requested_entities
    ]
    if not ordered_entities:
        raise ValidationError(
            "No enabled entity types are available for sync.",
            details={
                "enabled_entities": list(config.enabled_entities or []),
                "requested_entities": list(entity_types or []),
            },
        )
    return ordered_entities


def _has_inflight_sync(
    config: ConnectorConfig,
    entity_types: list[str],
) -> bool:
    return SyncLog.objects.filter(
        connector=config,
        entity_type__in=entity_types,
        status__in=[SyncStatus.PENDING, SyncStatus.RUNNING],
    ).exists()


def _mark_sync_logs_failed(logs: list[SyncLog], exc: Exception) -> None:
    if not logs:
        return

    now = timezone.now()
    for log in logs:
        log.status = SyncStatus.FAILED
        log.started_at = log.started_at or now
        log.completed_at = now
        entry = {"error": str(exc), "type": "dispatch"}
        details = getattr(exc, "details", None)
        if details is not None:
            entry["details"] = sanitize_for_log(details)
        log.error_details = [entry]
        log.save(
            update_fields=[
                "status",
                "started_at",
                "completed_at",
                "error_details",
                "updated_at",
            ]
        )


def _queue_sync(
    config: ConnectorConfig,
    entity_types: list[str] | None = None,
) -> QueuedSync:
    ordered_entities = _normalize_entity_types(config, entity_types)

    with transaction.atomic():
        if _has_inflight_sync(config, ordered_entities):
            raise ValidationError(
                "A sync for this connector is already queued or running.",
                details={"connector_id": str(config.id), "entity_types": ordered_entities},
            )

        logs = [
            SyncLog.objects.create(
                connector=config,
                org=config.org,
                entity_type=entity_type,
                status=SyncStatus.PENDING,
            )
            for entity_type in ordered_entities
        ]

    from app.connectors.tasks import run_connector_sync_task

    try:
        async_result = run_connector_sync_task.delay(
            str(config.id),
            [str(log.id) for log in logs],
            ordered_entities,
        )
    except Exception as exc:
        _mark_sync_logs_failed(logs, exc)
        raise ServiceUnavailableError(
            "Unable to queue connector sync.",
            details={"connector_id": str(config.id), "error": str(exc)},
        ) from exc

    return QueuedSync(logs=logs, task_id=str(getattr(async_result, "id", "")))


def _is_sync_due(config: ConnectorConfig, now) -> bool:
    if not config.enabled_entities:
        return False
    if config.last_synced_at is None:
        return True
    interval = max(1, config.sync_interval_minutes)
    return config.last_synced_at <= now - timedelta(minutes=interval)


# ------------------------------------------------------------------
# ConnectorConfig
# ------------------------------------------------------------------

def create_connector(org: Organization, data: dict, user: str = "") -> ConnectorConfig:
    connector_type = data.get("connector_type")
    if connector_type not in ConnectorType.values:
        raise ValidationError(f"Invalid connector_type: {connector_type}")

    try:
        return ConnectorConfig.objects.create(
            org=org,
            created_by=user,
            updated_by=user,
            **data,
        )
    except IntegrityError:
        raise ValidationError(
            f"Connector with name '{data.get('name')}' already exists in org '{org.id}'."
        )


def get_connector(org: Organization, connector_id: uuid.UUID) -> ConnectorConfig:
    try:
        return ConnectorConfig.objects.get(org=org, id=connector_id)
    except ConnectorConfig.DoesNotExist:
        raise EntityNotFoundError(f"Connector '{connector_id}' not found.")


def update_connector(
    org: Organization, connector_id: uuid.UUID, data: dict, user: str = "",
) -> ConnectorConfig:
    connector = get_connector(org, connector_id)
    for key, value in data.items():
        if value is not None:
            setattr(connector, key, value)
    connector.updated_by = user
    connector.save()
    return connector


def list_connectors(org: Organization) -> list[ConnectorConfig]:
    return list(
        ConnectorConfig.objects.filter(org=org).order_by("-created_at")
    )


def deactivate_connector(
    org: Organization, connector_id: uuid.UUID, user: str = "",
) -> ConnectorConfig:
    connector = get_connector(org, connector_id)
    connector.is_active = False
    connector.updated_by = user
    connector.save(update_fields=["is_active", "updated_by", "updated_at"])
    return connector


# ------------------------------------------------------------------
# Test connection
# ------------------------------------------------------------------

def test_connector_connection(
    org: Organization, connector_id: uuid.UUID,
) -> dict:
    from app.connectors.sync_orchestrator import _get_connector_instance

    config = get_connector(org, connector_id)
    instance = _get_connector_instance(config)
    try:
        return instance.test_connection()
    finally:
        if hasattr(instance, "close"):
            instance.close()


# ------------------------------------------------------------------
# Sync
# ------------------------------------------------------------------

def trigger_sync(
    org: Organization,
    connector_id: uuid.UUID,
    entity_types: list[str] | None = None,
) -> QueuedSync:
    config = get_connector(org, connector_id)
    if not config.is_active:
        raise ValidationError("Cannot sync an inactive connector.")
    return _queue_sync(config, entity_types=entity_types)


def execute_queued_sync(
    connector_id: str,
    sync_log_ids: list[str] | None = None,
    entity_types: list[str] | None = None,
) -> dict:
    try:
        config = ConnectorConfig.objects.select_related("org", "facility").get(id=connector_id)
    except ConnectorConfig.DoesNotExist as exc:
        raise EntityNotFoundError(f"Connector '{connector_id}' not found.") from exc

    sync_logs = list(
        SyncLog.objects.filter(connector=config, id__in=sync_log_ids or [])
        .order_by("created_at")
    )
    sync_logs_by_entity = {log.entity_type: log for log in sync_logs}
    resolved_entity_types = entity_types or [log.entity_type for log in sync_logs]

    if not config.is_active:
        exc = ValidationError("Cannot sync an inactive connector.")
        _mark_sync_logs_failed(sync_logs, exc)
        raise exc

    try:
        completed_logs = run_sync(
            config,
            entity_types=resolved_entity_types or None,
            sync_logs_by_entity=sync_logs_by_entity,
        )
    except Exception as exc:
        _mark_sync_logs_failed(sync_logs, exc)
        raise

    return {
        "connector_id": str(config.id),
        "entity_types": [log.entity_type for log in completed_logs],
        "log_ids": [str(log.id) for log in completed_logs],
    }


def dispatch_due_syncs() -> dict:
    now = timezone.now()
    queued = 0
    skipped = 0
    task_ids: list[str] = []
    errors: list[dict[str, str]] = []

    connectors = list(
        ConnectorConfig.objects.filter(is_active=True).select_related("org", "facility")
    )
    for config in connectors:
        if not _is_sync_due(config, now):
            skipped += 1
            continue

        try:
            queued_sync = _queue_sync(config)
            queued += 1
            task_ids.append(queued_sync.task_id)
        except ValidationError as exc:
            skipped += 1
            logger.info(
                "Skipping scheduled connector sync: connector=%s reason=%s",
                config.id,
                exc,
            )
        except Exception as exc:
            errors.append(
                {"connector_id": str(config.id), "error": str(exc)}
            )
            logger.exception(
                "Failed to queue scheduled connector sync: connector=%s",
                config.id,
            )

    return {
        "queued": queued,
        "skipped": skipped,
        "task_ids": task_ids,
        "errors": errors,
    }


# ------------------------------------------------------------------
# SyncLog queries
# ------------------------------------------------------------------

def list_sync_logs(
    org: Organization, connector_id: uuid.UUID, limit: int = 50,
) -> list[SyncLog]:
    connector = get_connector(org, connector_id)
    return list(
        SyncLog.objects.filter(connector=connector)
        .order_by("-created_at")[:limit]
    )


def get_sync_log(
    org: Organization, connector_id: uuid.UUID, log_id: uuid.UUID,
) -> SyncLog:
    connector = get_connector(org, connector_id)
    try:
        return SyncLog.objects.get(connector=connector, id=log_id)
    except SyncLog.DoesNotExist:
        raise EntityNotFoundError(f"SyncLog '{log_id}' not found.")
