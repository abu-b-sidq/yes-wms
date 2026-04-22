from __future__ import annotations

from ninja import Router

from app.auth.authorization import authorize_request, enforce_facility_scope
from app.auth.permissions import (
    PERM_INVENTORY_READ,
    PERM_OPERATIONS_EXECUTE,
    PERM_TRANSACTIONS_MANAGE,
    PERM_TRANSACTIONS_READ,
)
from app.core.openapi import protected_openapi_extra, register_response_schema
from app.core.response import success_response
from app.core.tenant import resolve_request_tenant
from app.operations import schemas, services

router = Router(tags=["operations"])

# ---------------------------------------------------------------------------
# Response data schemas — registered globally for Swagger 200 response bodies
# ---------------------------------------------------------------------------

_ENTITY_TYPE_ENUM = ["LOCATION", "ZONE", "INVOICE", "VIRTUAL_BUCKET", "SUPPLIER", "CUSTOMER"]

_PICK_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "sku_code": {"type": "string"},
        "source_entity_type": {"type": "string", "enum": _ENTITY_TYPE_ENUM},
        "source_entity_code": {"type": "string"},
        "quantity": {"type": "string", "format": "decimal"},
        "batch_number": {"type": "string"},
        "created_by": {"type": "string"},
        "performed_by": {"type": "string"},
    },
}

_DROP_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "sku_code": {"type": "string"},
        "dest_entity_type": {"type": "string", "enum": _ENTITY_TYPE_ENUM},
        "dest_entity_code": {"type": "string"},
        "quantity": {"type": "string", "format": "decimal"},
        "batch_number": {"type": "string"},
        "paired_pick_id": {"type": "string", "format": "uuid", "nullable": True},
        "created_by": {"type": "string"},
        "performed_by": {"type": "string"},
    },
}

_TXN_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "transaction_type": {
            "type": "string",
            "enum": ["MOVE", "ORDER_PICK", "GRN", "PUTAWAY", "RETURN", "CYCLE_COUNT", "ADJUSTMENT"],
        },
        "status": {
            "type": "string",
            "enum": ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED", "PARTIALLY_COMPLETED"],
        },
        "reference_number": {"type": "string"},
        "notes": {"type": "string"},
        "picks": {"type": "array", "items": _PICK_SCHEMA},
        "drops": {"type": "array", "items": _DROP_SCHEMA},
        "document_url": {
            "type": "string",
            "format": "uri",
            "description": (
                "Firebase Storage URL of the generated HTML document. "
                "Populated after execution when document generation is configured."
            ),
        },
        "started_at": {"type": "string", "format": "date-time", "nullable": True},
        "completed_at": {"type": "string", "format": "date-time", "nullable": True},
        "cancelled_at": {"type": "string", "format": "date-time", "nullable": True},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
        "created_by": {"type": "string"},
    },
}

_TXN_LIST_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "type": {
            "type": "string",
            "enum": ["MOVE", "ORDER_PICK", "GRN", "PUTAWAY", "RETURN", "CYCLE_COUNT", "ADJUSTMENT"],
        },
        "status": {
            "type": "string",
            "enum": ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED", "PARTIALLY_COMPLETED"],
        },
        "reference": {"type": "string", "nullable": True},
        "facility": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
}

_TXN_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {"type": "array", "items": _TXN_LIST_ITEM_SCHEMA},
        "total": {"type": "integer"},
        "page": {"type": "integer"},
        "size": {"type": "integer"},
    },
}

_VIRTUAL_WAREHOUSE_AREA_SCHEMA = {
    "type": "object",
    "properties": {
        "key": {"type": "string"},
        "label": {"type": "string"},
        "kind": {"type": "string"},
        "x": {"type": "integer"},
        "y": {"type": "integer"},
        "w": {"type": "integer"},
        "h": {"type": "integer"},
    },
}

_VIRTUAL_WAREHOUSE_ZONE_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "name": {"type": "string"},
        "kind": {"type": "string"},
        "label": {"type": "string"},
        "x": {"type": "integer"},
        "y": {"type": "integer"},
        "w": {"type": "integer"},
        "h": {"type": "integer"},
    },
}

_VIRTUAL_WAREHOUSE_STOCK_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "sku_code": {"type": "string"},
        "sku_name": {"type": "string"},
        "batch_number": {"type": "string"},
        "quantity_on_hand": {"type": "string", "format": "decimal"},
        "quantity_available": {"type": "string", "format": "decimal"},
        "quantity_reserved": {"type": "string", "format": "decimal"},
    },
}

_VIRTUAL_WAREHOUSE_TASK_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "task_type": {"type": "string"},
        "task_status": {"type": "string"},
        "transaction_id": {"type": "string", "format": "uuid"},
        "transaction_type": {"type": "string"},
        "reference_number": {"type": "string"},
        "sku_code": {"type": "string"},
        "sku_name": {"type": "string"},
        "quantity": {"type": "string", "format": "decimal"},
        "counterpart_entity_code": {"type": "string", "nullable": True},
        "assigned_to_name": {"type": "string", "nullable": True},
        "picked_by_name": {"type": "string", "nullable": True},
        "task_started_at": {"type": "string", "format": "date-time", "nullable": True},
        "task_completed_at": {"type": "string", "format": "date-time", "nullable": True},
    },
}

_VIRTUAL_WAREHOUSE_LOCATION_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "name": {"type": "string"},
        "zone_code": {"type": "string"},
        "kind": {"type": "string"},
        "x": {"type": "integer"},
        "y": {"type": "integer"},
        "w": {"type": "integer"},
        "h": {"type": "integer"},
        "rotation": {"type": "integer"},
        "quantity_on_hand": {"type": "string", "format": "decimal"},
        "quantity_available": {"type": "string", "format": "decimal"},
        "quantity_reserved": {"type": "string", "format": "decimal"},
        "stock_items": {"type": "array", "items": _VIRTUAL_WAREHOUSE_STOCK_ITEM_SCHEMA},
        "active_tasks": {"type": "array", "items": _VIRTUAL_WAREHOUSE_TASK_SUMMARY_SCHEMA},
        "worker_ids": {"type": "array", "items": {"type": "string"}},
    },
}

_VIRTUAL_WAREHOUSE_WORKER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "user_id": {"type": "string"},
        "display_name": {"type": "string"},
        "state": {"type": "string"},
        "x": {"type": "integer"},
        "y": {"type": "integer"},
        "task_id": {"type": "string", "format": "uuid"},
        "task_type": {"type": "string"},
        "task_status": {"type": "string"},
        "sku_code": {"type": "string"},
        "sku_name": {"type": "string"},
        "quantity": {"type": "string", "format": "decimal"},
        "source_entity_type": {"type": "string", "nullable": True},
        "source_entity_code": {"type": "string", "nullable": True},
        "dest_entity_type": {"type": "string", "nullable": True},
        "dest_entity_code": {"type": "string", "nullable": True},
        "assigned_at": {"type": "string", "format": "date-time", "nullable": True},
        "task_started_at": {"type": "string", "format": "date-time", "nullable": True},
        "task_completed_at": {"type": "string", "format": "date-time", "nullable": True},
    },
}

_VIRTUAL_WAREHOUSE_TASK_LINK_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "state": {"type": "string"},
        "worker_id": {"type": "string"},
        "worker_name": {"type": "string"},
        "sku_code": {"type": "string"},
        "quantity": {"type": "string", "format": "decimal"},
        "source_entity_type": {"type": "string"},
        "source_entity_code": {"type": "string"},
        "dest_entity_type": {"type": "string"},
        "dest_entity_code": {"type": "string"},
        "source_x": {"type": "integer"},
        "source_y": {"type": "integer"},
        "dest_x": {"type": "integer"},
        "dest_y": {"type": "integer"},
    },
}

_VIRTUAL_WAREHOUSE_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "location_quantity": {"type": "string", "format": "decimal"},
        "user_quantity": {"type": "string", "format": "decimal"},
        "workers_active": {"type": "integer"},
        "workers_carrying": {"type": "integer"},
        "locations_with_stock": {"type": "integer"},
        "unplaced_location_count": {"type": "integer"},
    },
}

_VIRTUAL_WAREHOUSE_UNPLACED_LOCATION_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "name": {"type": "string"},
        "zone_code": {"type": "string"},
    },
}

_VIRTUAL_WAREHOUSE_SCHEMA = {
    "type": "object",
    "properties": {
        "facility": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "name": {"type": "string"},
                "warehouse_key": {"type": "string"},
            },
        },
        "scene": {
            "type": "object",
            "properties": {
                "width": {"type": "integer"},
                "height": {"type": "integer"},
                "areas": {"type": "array", "items": _VIRTUAL_WAREHOUSE_AREA_SCHEMA},
            },
        },
        "zones": {"type": "array", "items": _VIRTUAL_WAREHOUSE_ZONE_SCHEMA},
        "locations": {"type": "array", "items": _VIRTUAL_WAREHOUSE_LOCATION_SCHEMA},
        "workers": {"type": "array", "items": _VIRTUAL_WAREHOUSE_WORKER_SCHEMA},
        "task_links": {"type": "array", "items": _VIRTUAL_WAREHOUSE_TASK_LINK_SCHEMA},
        "summary": _VIRTUAL_WAREHOUSE_SUMMARY_SCHEMA,
        "unplaced_locations": {"type": "array", "items": _VIRTUAL_WAREHOUSE_UNPLACED_LOCATION_SCHEMA},
    },
}

# ---------------------------------------------------------------------------
# openapi_extra presets
# ---------------------------------------------------------------------------

ORG_PROTECTED = protected_openapi_extra()
ORG_WITH_OPTIONAL_FACILITY = protected_openapi_extra(include_facility=True)
ORG_WITH_REQUIRED_FACILITY = protected_openapi_extra(require_facility=True)

# ---------------------------------------------------------------------------
# Transaction CRUD
# ---------------------------------------------------------------------------

@router.post(
    "/transactions",
    summary="Create transaction",
    description=(
        "Create a new transaction with picks and drops in `PENDING` status. "
        "Must be explicitly executed to affect inventory.\n\n"
        "**Transaction types:** `MOVE`, `ORDER_PICK`, `GRN`, `PUTAWAY`, `RETURN`, `CYCLE_COUNT`, `ADJUSTMENT`"
    ),
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def create_transaction(request, payload: schemas.TransactionCreateIn):
    authorize_request(
        request,
        PERM_TRANSACTIONS_MANAGE,
        require_membership=True,
    )
    org, facility = resolve_request_tenant(request, require_facility=True)
    user = _get_user(request)
    txn = services.create_transaction(org, facility, payload.dict(), user=user)
    return success_response(request, data=_txn_out(txn))


@router.get(
    "/transactions",
    summary="List transactions",
    description=(
        "List transactions for the organisation, optionally filtered by facility, type, or status. "
        "Returns the most recent 100 transactions ordered by creation date descending."
    ),
    openapi_extra=ORG_WITH_OPTIONAL_FACILITY,
)
def list_transactions(
    request,
    transaction_type: str | None = None,
    status: str | None = None,
):
    authorize_request(
        request,
        PERM_TRANSACTIONS_READ,
        require_membership=True,
        require_optional_facility_header=True,
    )
    org, facility = resolve_request_tenant(request)
    page = _positive_int_param(request, "page", 1)
    size = _positive_int_param(request, "size", 25, maximum=100)
    txns, total = services.list_transactions(
        org, facility=facility, transaction_type=transaction_type, status=status,
        page=page, size=size,
    )
    return success_response(request, data={
        "items": [_txn_list_out(t) for t in txns],
        "total": total,
        "page": page,
        "size": size,
    })


@router.get(
    "/transactions/{txn_id}",
    summary="Get transaction",
    description="Retrieve a single transaction by ID, including all picks, drops, and document URL.",
    openapi_extra=ORG_PROTECTED,
)
def get_transaction(request, txn_id: str):
    access = authorize_request(
        request,
        PERM_TRANSACTIONS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    txn = services.get_transaction(org, txn_id)
    enforce_facility_scope(access, txn.facility.code)
    return success_response(request, data=_txn_out(txn))


@router.post(
    "/transactions/{txn_id}/execute",
    summary="Execute transaction",
    description=(
        "Execute a `PENDING` transaction: atomically apply all inventory debits (picks) and credits (drops), "
        "then transition to `COMPLETED`.\n\n"
        "**Document generation:** if configured for this org/facility/type, an HTML document is rendered "
        "and uploaded to Firebase Storage. The URL is returned in `data.document_url`."
    ),
    openapi_extra=ORG_PROTECTED,
)
def execute_transaction(request, txn_id: str):
    access = authorize_request(
        request,
        PERM_TRANSACTIONS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    txn = services.get_transaction(org, txn_id)
    enforce_facility_scope(access, txn.facility.code)
    user = _get_user(request)
    txn = services.execute_transaction(txn, user=user)
    return success_response(request, data=_txn_out(txn))


@router.post(
    "/transactions/{txn_id}/cancel",
    summary="Cancel transaction",
    description=(
        "Cancel a transaction. Only `PENDING` or `IN_PROGRESS` transactions can be cancelled. "
        "Cancelled transactions do not affect inventory balances."
    ),
    openapi_extra=ORG_PROTECTED,
)
def cancel_transaction(request, txn_id: str):
    access = authorize_request(
        request,
        PERM_TRANSACTIONS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    txn = services.get_transaction(org, txn_id)
    enforce_facility_scope(access, txn.facility.code)
    txn = services.cancel_transaction(txn)
    return success_response(request, data=_txn_out(txn))


# ---------------------------------------------------------------------------
# Convenience endpoints (create + execute in one call)
# ---------------------------------------------------------------------------

@router.post(
    "/move",
    summary="Move inventory",
    description=(
        "Create and immediately execute a `MOVE` transaction "
        "that transfers a SKU from one location to another."
    ),
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def move(request, payload: schemas.MoveIn):
    authorize_request(
        request,
        PERM_OPERATIONS_EXECUTE,
        require_membership=True,
    )
    org, facility = resolve_request_tenant(request, require_facility=True)
    user = _get_user(request)
    txn = services.create_and_execute_move(org, facility, payload.dict(), user=user)
    return success_response(request, data=_txn_out(txn))


@router.post(
    "/grn",
    summary="Goods Received Note",
    description=(
        "Create and immediately execute a `GRN` transaction to receive one or more SKUs "
        "into the `PRE_PUTAWAY` zone (or a specified zone). No picks required."
    ),
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def grn(request, payload: schemas.GRNIn):
    authorize_request(
        request,
        PERM_OPERATIONS_EXECUTE,
        require_membership=True,
    )
    org, facility = resolve_request_tenant(request, require_facility=True)
    user = _get_user(request)
    txn = services.create_and_execute_grn(org, facility, payload.dict(), user=user)
    return success_response(request, data=_txn_out(txn))


@router.post(
    "/putaway",
    summary="Putaway",
    description=(
        "Create and immediately execute a `PUTAWAY` transaction that moves a SKU "
        "from a staging zone (default `PRE_PUTAWAY`) to a storage location."
    ),
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def putaway(request, payload: schemas.PutawayIn):
    authorize_request(
        request,
        PERM_OPERATIONS_EXECUTE,
        require_membership=True,
    )
    org, facility = resolve_request_tenant(request, require_facility=True)
    user = _get_user(request)
    txn = services.create_and_execute_putaway(org, facility, payload.dict(), user=user)
    return success_response(request, data=_txn_out(txn))


@router.post(
    "/order-pick",
    summary="Order pick",
    description=(
        "Create and immediately execute an `ORDER_PICK` transaction that picks a SKU "
        "from a storage location and assigns it to an invoice (order)."
    ),
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def order_pick(request, payload: schemas.OrderPickIn):
    authorize_request(
        request,
        PERM_OPERATIONS_EXECUTE,
        require_membership=True,
    )
    org, facility = resolve_request_tenant(request, require_facility=True)
    user = _get_user(request)
    txn = services.create_and_execute_order_pick(org, facility, payload.dict(), user=user)
    return success_response(request, data=_txn_out(txn))


@router.get(
    "/virtual-warehouse",
    summary="Virtual warehouse scene",
    description=(
        "Return a facility-scoped virtual warehouse scene that combines configured layout metadata, "
        "live inventory by location, and worker/task overlays."
    ),
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def virtual_warehouse(request):
    authorize_request(
        request,
        PERM_INVENTORY_READ,
        require_membership=True,
    )
    org, facility = resolve_request_tenant(request, require_facility=True)
    return success_response(
        request,
        data=schemas.VirtualWarehouseOut(**services.get_virtual_warehouse(org, facility)).dict(),
    )


# ---------------------------------------------------------------------------
# Register response schemas (used by inject_security_schemes for Swagger docs)
# ---------------------------------------------------------------------------

register_response_schema("app_operations_routes_create_transaction", _TXN_SCHEMA)
register_response_schema("app_operations_routes_list_transactions", _TXN_LIST_SCHEMA)
register_response_schema("app_operations_routes_get_transaction", _TXN_SCHEMA)
register_response_schema("app_operations_routes_execute_transaction", _TXN_SCHEMA)
register_response_schema("app_operations_routes_cancel_transaction", _TXN_SCHEMA)
register_response_schema("app_operations_routes_move", _TXN_SCHEMA)
register_response_schema("app_operations_routes_grn", _TXN_SCHEMA)
register_response_schema("app_operations_routes_putaway", _TXN_SCHEMA)
register_response_schema("app_operations_routes_order_pick", _TXN_SCHEMA)
register_response_schema("app_operations_routes_virtual_warehouse", _VIRTUAL_WAREHOUSE_SCHEMA)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _positive_int_param(request, key: str, default: int, *, maximum: int | None = None) -> int:
    raw_value = request.GET.get(key)
    try:
        value = int(raw_value) if raw_value is not None else default
    except (TypeError, ValueError):
        value = default
    value = max(value, 1)
    if maximum is not None:
        value = min(value, maximum)
    return value


def _get_user(request) -> str:
    auth = getattr(request, "auth_context", None)
    if auth and auth.uid:
        return auth.uid
    if auth and auth.client_name:
        return auth.client_name
    return ""


def _txn_list_out(txn) -> dict:
    """Lightweight list-item shape matching the frontend TransactionListItem model."""
    return {
        "id": str(txn.id),
        "type": txn.transaction_type,
        "status": txn.status,
        "reference": txn.reference_number or None,
        "facility": txn.facility.code,
        "created_at": txn.created_at.isoformat(),
        "updated_at": txn.updated_at.isoformat(),
    }


def _txn_out(txn) -> dict:
    picks = []
    for p in txn.picks.all():
        picks.append(
            schemas.PickOut(
                id=str(p.id),
                sku_code=p.sku.code,
                source_entity_type=p.source_entity_type,
                source_entity_code=p.source_entity_code,
                quantity=p.quantity,
                batch_number=p.batch_number,
                created_by=p.created_by,
                performed_by=p.performed_by,
            ).dict()
        )
    drops = []
    for d in txn.drops.all():
        drops.append(
            schemas.DropOut(
                id=str(d.id),
                sku_code=d.sku.code,
                dest_entity_type=d.dest_entity_type,
                dest_entity_code=d.dest_entity_code,
                quantity=d.quantity,
                batch_number=d.batch_number,
                paired_pick_id=str(d.paired_pick_id) if d.paired_pick_id else None,
                created_by=d.created_by,
                performed_by=d.performed_by,
            ).dict()
        )
    return schemas.TransactionOut(
        id=str(txn.id),
        transaction_type=txn.transaction_type,
        status=txn.status,
        reference_number=txn.reference_number,
        notes=txn.notes,
        picks=picks,
        drops=drops,
        started_at=txn.started_at,
        completed_at=txn.completed_at,
        cancelled_at=txn.cancelled_at,
        created_at=txn.created_at,
        updated_at=txn.updated_at,
        document_url=txn.document_url or "",
        created_by=txn.created_by,
    ).dict()
