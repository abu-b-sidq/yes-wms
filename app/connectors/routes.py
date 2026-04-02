from __future__ import annotations

from uuid import UUID

from asgiref.sync import sync_to_async
from django.http import JsonResponse
from ninja import Router

from app.auth.authorization import authorize_request
from app.core.openapi import protected_openapi_extra
from app.core.response import success_response
from app.core.tenant import resolve_request_tenant
from app.connectors import schemas, services

router = Router(tags=["connectors"])


def _get_user(request) -> str:
    auth = getattr(request, "auth_context", None)
    if auth and auth.uid:
        return auth.uid
    if auth and auth.client_name:
        return auth.client_name
    return ""


def _connector_out(c) -> dict:
    return schemas.ConnectorConfigOut(
        id=c.id,
        name=c.name,
        connector_type=c.connector_type,
        is_active=c.is_active,
        facility_id=c.facility_id,
        config=c.config,
        sync_interval_minutes=c.sync_interval_minutes,
        enabled_entities=c.enabled_entities,
        last_synced_at=c.last_synced_at.isoformat() if c.last_synced_at else None,
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
    ).dict()


def _sync_log_out(log) -> dict:
    return schemas.SyncLogOut(
        id=log.id,
        connector_id=log.connector_id,
        entity_type=log.entity_type,
        status=log.status,
        started_at=log.started_at.isoformat() if log.started_at else None,
        completed_at=log.completed_at.isoformat() if log.completed_at else None,
        records_fetched=log.records_fetched,
        records_created=log.records_created,
        records_updated=log.records_updated,
        records_skipped=log.records_skipped,
        records_failed=log.records_failed,
        error_details=log.error_details,
        created_at=log.created_at.isoformat(),
    ).dict()


# ------------------------------------------------------------------
# CRUD — ConnectorConfig
# ------------------------------------------------------------------

@router.post(
    "/",
    summary="Create connector",
    openapi_extra=protected_openapi_extra(),
)
def create_connector(request, payload: schemas.ConnectorConfigCreateIn):
    authorize_request(request, require_membership=True)
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    data = payload.dict()
    # Map facility_id → facility FK
    facility_id = data.pop("facility_id", None)
    if facility_id:
        from app.masters.models import Facility
        data["facility"] = Facility.objects.get(org=org, id=facility_id)
    connector = services.create_connector(org, data, user=user)
    return success_response(request, data=_connector_out(connector))


@router.get(
    "/",
    summary="List connectors",
    openapi_extra=protected_openapi_extra(),
)
def list_connectors(request):
    authorize_request(request, require_membership=True)
    org, _ = resolve_request_tenant(request)
    connectors = services.list_connectors(org)
    return success_response(
        request, data=[_connector_out(c) for c in connectors],
    )


@router.get(
    "/{connector_id}",
    summary="Get connector",
    openapi_extra=protected_openapi_extra(),
)
def get_connector(request, connector_id: UUID):
    authorize_request(request, require_membership=True)
    org, _ = resolve_request_tenant(request)
    connector = services.get_connector(org, connector_id)
    return success_response(request, data=_connector_out(connector))


@router.put(
    "/{connector_id}",
    summary="Update connector",
    openapi_extra=protected_openapi_extra(),
)
def update_connector(request, connector_id: UUID, payload: schemas.ConnectorConfigUpdateIn):
    authorize_request(request, require_membership=True)
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    data = payload.dict(exclude_unset=True)
    facility_id = data.pop("facility_id", None)
    if facility_id:
        from app.masters.models import Facility
        data["facility"] = Facility.objects.get(org=org, id=facility_id)
    connector = services.update_connector(org, connector_id, data, user=user)
    return success_response(request, data=_connector_out(connector))


@router.delete(
    "/{connector_id}",
    summary="Deactivate connector",
    openapi_extra=protected_openapi_extra(),
)
def deactivate_connector(request, connector_id: UUID):
    authorize_request(request, require_membership=True)
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    connector = services.deactivate_connector(org, connector_id, user=user)
    return success_response(request, data=_connector_out(connector))


# ------------------------------------------------------------------
# Test connection
# ------------------------------------------------------------------

@router.post(
    "/{connector_id}/test",
    summary="Test connector connection",
    openapi_extra=protected_openapi_extra(),
)
def test_connection(request, connector_id: UUID):
    authorize_request(request, require_membership=True)
    org, _ = resolve_request_tenant(request)
    result = services.test_connector_connection(org, connector_id)
    return success_response(request, data=result)


# ------------------------------------------------------------------
# Sync
# ------------------------------------------------------------------

@router.post(
    "/{connector_id}/sync",
    summary="Queue connector sync",
    openapi_extra=protected_openapi_extra(),
)
async def trigger_sync(
    request,
    connector_id: UUID,
    payload: schemas.SyncTriggerIn | None = None,
):
    await sync_to_async(authorize_request)(request, require_membership=True)
    org, _ = await sync_to_async(resolve_request_tenant)(request)
    entity_types = payload.entity_types if payload else None
    queued_sync = await sync_to_async(services.trigger_sync)(
        org,
        connector_id,
        entity_types=entity_types,
    )
    return JsonResponse(
        success_response(
            request,
            data=[_sync_log_out(log) for log in queued_sync.logs],
            extra_meta={"task_id": queued_sync.task_id},
        ),
        status=202,
    )


# ------------------------------------------------------------------
# Sync logs
# ------------------------------------------------------------------

@router.get(
    "/{connector_id}/logs",
    summary="List sync logs",
    openapi_extra=protected_openapi_extra(),
)
def list_sync_logs(request, connector_id: UUID):
    authorize_request(request, require_membership=True)
    org, _ = resolve_request_tenant(request)
    logs = services.list_sync_logs(org, connector_id)
    return success_response(
        request, data=[_sync_log_out(log) for log in logs],
    )


@router.get(
    "/{connector_id}/logs/{log_id}",
    summary="Get sync log detail",
    openapi_extra=protected_openapi_extra(),
)
def get_sync_log(request, connector_id: UUID, log_id: UUID):
    authorize_request(request, require_membership=True)
    org, _ = resolve_request_tenant(request)
    log = services.get_sync_log(org, connector_id, log_id)
    return success_response(request, data=_sync_log_out(log))
