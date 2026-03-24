from __future__ import annotations

from ninja import Router

from app.core.openapi import protected_openapi_extra, success_response_schema
from app.core.response import success_response
from app.core.tenant import resolve_request_tenant
from app.inventory import schemas, services

router = Router(tags=["inventory"])

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

_ENTITY_TYPE_ENUM = ["LOCATION", "ZONE", "INVOICE", "VIRTUAL_BUCKET", "SUPPLIER", "CUSTOMER"]

_BALANCE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "facility_code": {"type": "string"},
        "sku_code": {"type": "string"},
        "entity_type": {"type": "string", "enum": _ENTITY_TYPE_ENUM},
        "entity_code": {"type": "string"},
        "batch_number": {"type": "string"},
        "quantity_on_hand": {"type": "string", "format": "decimal"},
        "quantity_reserved": {"type": "string", "format": "decimal"},
        "quantity_available": {
            "type": "string",
            "format": "decimal",
            "description": "quantity_on_hand minus quantity_reserved.",
        },
        "updated_at": {"type": "string", "format": "date-time"},
    },
}

_LEDGER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "facility_code": {"type": "string"},
        "sku_code": {"type": "string"},
        "transaction_id": {"type": "string", "format": "uuid"},
        "entry_type": {"type": "string", "enum": ["PICK", "DROP"]},
        "entity_type": {"type": "string", "enum": _ENTITY_TYPE_ENUM},
        "entity_code": {"type": "string"},
        "batch_number": {"type": "string"},
        "quantity": {
            "type": "string",
            "format": "decimal",
            "description": "Signed quantity — negative for picks, positive for drops.",
        },
        "balance_after": {"type": "string", "format": "decimal"},
        "created_at": {"type": "string", "format": "date-time"},
    },
}

_BALANCES_RESPONSE = success_response_schema({"type": "array", "items": _BALANCE_SCHEMA})
_LEDGER_RESPONSE = success_response_schema({"type": "array", "items": _LEDGER_SCHEMA})

ORG_WITH_OPTIONAL_FACILITY = protected_openapi_extra(include_facility=True)
ORG_WITH_REQUIRED_FACILITY = protected_openapi_extra(require_facility=True)


# ---------------------------------------------------------------------------
# Balances
# ---------------------------------------------------------------------------

@router.get(
    "/balances",
    summary="Query inventory balances",
    description=(
        "Return current stock levels filtered by optional SKU, entity type, or entity code. "
        "Pass `X-Facility-Id` to scope results to a specific facility."
    ),
    openapi_extra=protected_openapi_extra(include_facility=True, response_schema=_BALANCES_RESPONSE),
)
def list_balances(
    request,
    sku_code: str | None = None,
    entity_type: str | None = None,
    entity_code: str | None = None,
):
    org, facility = resolve_request_tenant(request)
    balances = services.get_balances(
        org, facility=facility, sku_code=sku_code,
        entity_type=entity_type, entity_code=entity_code,
    )
    return success_response(request, data=[_balance_out(b) for b in balances])


@router.get(
    "/balances/by-location/{code}",
    summary="Inventory at a specific location",
    description="Return all SKU balances at the given storage location within a facility.",
    openapi_extra=protected_openapi_extra(require_facility=True, response_schema=_BALANCES_RESPONSE),
)
def balances_by_location(request, code: str):
    org, facility = resolve_request_tenant(request, require_facility=True)
    balances = services.get_balances_by_location(org, facility, code)
    return success_response(request, data=[_balance_out(b) for b in balances])


@router.get(
    "/balances/by-sku/{code}",
    summary="Inventory for a SKU across locations",
    description="Return balances for a specific SKU across all locations in a facility.",
    openapi_extra=protected_openapi_extra(require_facility=True, response_schema=_BALANCES_RESPONSE),
)
def balances_by_sku(request, code: str):
    org, facility = resolve_request_tenant(request, require_facility=True)
    balances = services.get_balances_by_sku(org, facility, code)
    return success_response(request, data=[_balance_out(b) for b in balances])


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------

@router.get(
    "/ledger",
    summary="Query inventory ledger",
    description=(
        "Return immutable ledger entries representing inventory debits (picks) and credits (drops). "
        "Filter by SKU or transaction ID. Quantity is signed: negative for picks, positive for drops."
    ),
    openapi_extra=protected_openapi_extra(include_facility=True, response_schema=_LEDGER_RESPONSE),
)
def list_ledger(
    request,
    sku_code: str | None = None,
    transaction_id: str | None = None,
):
    org, facility = resolve_request_tenant(request)
    entries = services.get_ledger(
        org, facility=facility, sku_code=sku_code, transaction_id=transaction_id,
    )
    return success_response(request, data=[_ledger_out(e) for e in entries])


@router.get(
    "/ledger/by-transaction/{txn_id}",
    summary="Ledger entries for a specific transaction",
    description="Return all ledger entries created by a single transaction execution.",
    openapi_extra=protected_openapi_extra(response_schema=_LEDGER_RESPONSE),
)
def ledger_by_transaction(request, txn_id: str):
    org, _ = resolve_request_tenant(request)
    entries = services.get_ledger(org, transaction_id=txn_id)
    return success_response(request, data=[_ledger_out(e) for e in entries])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _balance_out(b) -> dict:
    return schemas.BalanceOut(
        id=str(b.id),
        facility_code=b.facility.code,
        sku_code=b.sku.code,
        entity_type=b.entity_type,
        entity_code=b.entity_code,
        batch_number=b.batch_number,
        quantity_on_hand=b.quantity_on_hand,
        quantity_reserved=b.quantity_reserved,
        quantity_available=b.quantity_available,
        updated_at=b.updated_at,
    ).dict()


def _ledger_out(e) -> dict:
    return schemas.LedgerEntryOut(
        id=str(e.id),
        facility_code=e.facility.code,
        sku_code=e.sku.code,
        transaction_id=str(e.transaction_id),
        entry_type=e.entry_type,
        entity_type=e.entity_type,
        entity_code=e.entity_code,
        batch_number=e.batch_number,
        quantity=e.quantity,
        balance_after=e.balance_after,
        created_at=e.created_at,
    ).dict()
