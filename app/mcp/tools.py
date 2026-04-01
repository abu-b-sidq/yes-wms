"""MCP tool implementations — thin async wrappers over Django WMS services."""
from __future__ import annotations

from decimal import Decimal

from asgiref.sync import sync_to_async


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def _org(o) -> dict:
    return {"id": o.id, "name": o.name, "is_active": o.is_active, "created_at": o.created_at.isoformat()}


def _facility(f) -> dict:
    return {
        "id": str(f.id), "code": f.code, "warehouse_key": f.warehouse_key,
        "name": f.name, "is_active": f.is_active, "address": f.address or "",
    }


def _sku(s) -> dict:
    return {
        "id": str(s.id), "code": s.code, "name": s.name,
        "unit_of_measure": s.unit_of_measure, "is_active": s.is_active,
        "metadata": s.metadata or {},
    }


def _zone(z) -> dict:
    return {"id": str(z.id), "code": z.code, "name": z.name, "is_active": z.is_active}


def _location(loc) -> dict:
    return {
        "id": str(loc.id), "code": loc.code, "name": loc.name,
        "zone_code": loc.zone.code if loc.zone_id else None,
        "is_active": loc.is_active, "capacity": loc.capacity,
    }


def _balance(b) -> dict:
    return {
        "id": str(b.id),
        "facility_code": b.facility.code if b.facility_id else None,
        "sku_code": b.sku.code,
        "entity_type": b.entity_type,
        "entity_code": b.entity_code,
        "batch_number": b.batch_number,
        "quantity_on_hand": str(b.quantity_on_hand),
        "quantity_reserved": str(b.quantity_reserved),
        "quantity_available": str(b.quantity_available),
        "updated_at": b.updated_at.isoformat(),
    }


def _ledger(e) -> dict:
    return {
        "id": str(e.id),
        "facility_code": e.facility.code if e.facility_id else None,
        "sku_code": e.sku.code,
        "transaction_id": str(e.transaction_id),
        "entry_type": e.entry_type,
        "entity_type": e.entity_type,
        "entity_code": e.entity_code,
        "batch_number": e.batch_number,
        "quantity": str(e.quantity),
        "balance_after": str(e.balance_after),
        "created_at": e.created_at.isoformat(),
    }


def _pick(p) -> dict:
    return {
        "id": str(p.id), "sku_code": p.sku.code,
        "source_entity_type": p.source_entity_type,
        "source_entity_code": p.source_entity_code,
        "quantity": str(p.quantity), "batch_number": p.batch_number,
    }


def _drop(d) -> dict:
    return {
        "id": str(d.id), "sku_code": d.sku.code,
        "dest_entity_type": d.dest_entity_type,
        "dest_entity_code": d.dest_entity_code,
        "quantity": str(d.quantity), "batch_number": d.batch_number,
        "paired_pick_id": str(d.paired_pick_id) if d.paired_pick_id else None,
    }


def _txn(t) -> dict:
    return {
        "id": str(t.id),
        "transaction_type": t.transaction_type,
        "status": t.status,
        "reference_number": t.reference_number,
        "notes": t.notes,
        "document_url": t.document_url or None,
        "picks": [_pick(p) for p in t.picks.all()],
        "drops": [_drop(d) for d in t.drops.all()],
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
        "started_at": t.started_at.isoformat() if t.started_at else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "cancelled_at": t.cancelled_at.isoformat() if t.cancelled_at else None,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_org(org_id: str):
    from app.masters.services import get_organization
    return get_organization(org_id)


def _resolve_facility(org, facility_id: str):
    from app.masters.services import get_facility
    return get_facility(org, facility_id)


def _check(uid: str, org_id: str | None, permission: str | None = None):
    """Resolve AccessContext and check permission. Raises AuthorizationError on failure."""
    from app.auth.authorization import get_mcp_access_context
    from app.core.exceptions import AuthorizationError
    access = get_mcp_access_context(uid, org_id)
    if permission and not access.is_platform_admin and permission not in access.permission_codes:
        raise AuthorizationError(
            "You do not have permission to perform this action.",
            code="AUTHZ_FORBIDDEN",
        )
    return access


# ---------------------------------------------------------------------------
# Masters tools
# ---------------------------------------------------------------------------

@sync_to_async
def wms_list_organizations(uid: str = "") -> list[dict]:
    from app.auth.authorization import get_mcp_access_context, active_membership_org_ids
    from app.masters.services import list_organizations
    access = get_mcp_access_context(uid, org_id=None)
    orgs = list_organizations()
    if not access.is_platform_admin:
        allowed = active_membership_org_ids(access.app_user)
        orgs = [o for o in orgs if o.id in allowed]
    return [_org(o) for o in orgs]


@sync_to_async
def wms_list_facilities(org_id: str, uid: str = "") -> list[dict]:
    from app.auth.permissions import PERM_MASTERS_READ
    from app.masters.services import list_facilities
    access = _check(uid, org_id, PERM_MASTERS_READ)
    org = _resolve_org(org_id)
    facilities = list_facilities(org)
    if access.allowed_facility_codes:
        facilities = [f for f in facilities if f.code in access.allowed_facility_codes]
    return [_facility(f) for f in facilities]


@sync_to_async
def wms_list_skus(org_id: str, uid: str = "") -> list[dict]:
    from app.auth.permissions import PERM_MASTERS_READ
    from app.masters.services import list_skus
    _check(uid, org_id, PERM_MASTERS_READ)
    org = _resolve_org(org_id)
    return [_sku(s) for s in list_skus(org)]


@sync_to_async
def wms_list_zones(org_id: str, uid: str = "") -> list[dict]:
    from app.auth.permissions import PERM_MASTERS_READ
    from app.masters.services import list_zones
    _check(uid, org_id, PERM_MASTERS_READ)
    org = _resolve_org(org_id)
    return [_zone(z) for z in list_zones(org)]


@sync_to_async
def wms_list_locations(org_id: str, uid: str = "") -> list[dict]:
    from app.auth.permissions import PERM_MASTERS_READ
    from app.masters.services import list_locations
    _check(uid, org_id, PERM_MASTERS_READ)
    org = _resolve_org(org_id)
    return [_location(loc) for loc in list_locations(org)]


# ---------------------------------------------------------------------------
# Inventory tools
# ---------------------------------------------------------------------------

@sync_to_async
def wms_get_inventory_balances(
    org_id: str,
    facility_id: str | None = None,
    sku_code: str | None = None,
    entity_type: str | None = None,
    entity_code: str | None = None,
    uid: str = "",
) -> list[dict]:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_INVENTORY_READ
    from app.core.exceptions import AuthorizationError
    from app.inventory.services import get_balances
    access = _check(uid, org_id, PERM_INVENTORY_READ)
    if not facility_id and access.allowed_facility_codes:
        raise AuthorizationError(
            "Facility-restricted users must specify facility_id.",
            code="AUTHZ_FACILITY_SCOPE_REQUIRED",
        )
    if facility_id:
        enforce_facility_scope(access, facility_id)
    org = _resolve_org(org_id)
    facility = _resolve_facility(org, facility_id) if facility_id else None
    return [_balance(b) for b in get_balances(org, facility=facility, sku_code=sku_code, entity_type=entity_type, entity_code=entity_code)]


@sync_to_async
def wms_get_inventory_ledger(
    org_id: str,
    facility_id: str | None = None,
    sku_code: str | None = None,
    transaction_id: str | None = None,
    uid: str = "",
) -> list[dict]:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_INVENTORY_READ
    from app.core.exceptions import AuthorizationError
    from app.inventory.services import get_ledger
    access = _check(uid, org_id, PERM_INVENTORY_READ)
    if not facility_id and access.allowed_facility_codes:
        raise AuthorizationError(
            "Facility-restricted users must specify facility_id.",
            code="AUTHZ_FACILITY_SCOPE_REQUIRED",
        )
    if facility_id:
        enforce_facility_scope(access, facility_id)
    org = _resolve_org(org_id)
    facility = _resolve_facility(org, facility_id) if facility_id else None
    return [_ledger(e) for e in get_ledger(org, facility=facility, sku_code=sku_code, transaction_id=transaction_id)]


# ---------------------------------------------------------------------------
# Transaction tools
# ---------------------------------------------------------------------------

@sync_to_async
def wms_list_transactions(
    org_id: str,
    facility_id: str | None = None,
    transaction_type: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    uid: str = "",
) -> list[dict]:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_TRANSACTIONS_READ
    from app.core.exceptions import AuthorizationError
    from app.operations.services import list_transactions
    access = _check(uid, org_id, PERM_TRANSACTIONS_READ)
    if not facility_id and access.allowed_facility_codes:
        raise AuthorizationError(
            "Facility-restricted users must specify facility_id.",
            code="AUTHZ_FACILITY_SCOPE_REQUIRED",
        )
    if facility_id:
        enforce_facility_scope(access, facility_id)
    org = _resolve_org(org_id)
    facility = _resolve_facility(org, facility_id) if facility_id else None
    return [_txn(t) for t in list_transactions(org, facility=facility, transaction_type=transaction_type, status=status, date_from=date_from, date_to=date_to)]


@sync_to_async
def wms_get_transaction(org_id: str, transaction_id: str, uid: str = "") -> dict:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_TRANSACTIONS_READ
    from app.operations.services import get_transaction
    access = _check(uid, org_id, PERM_TRANSACTIONS_READ)
    org = _resolve_org(org_id)
    txn = get_transaction(org, transaction_id)
    enforce_facility_scope(access, txn.facility.code)
    return _txn(txn)


@sync_to_async
def wms_create_transaction(
    org_id: str,
    facility_id: str,
    transaction_type: str,
    picks: list[dict],
    drops: list[dict],
    reference_number: str = "",
    notes: str = "",
    uid: str = "",
) -> dict:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_TRANSACTIONS_MANAGE
    from app.operations.services import create_transaction
    access = _check(uid, org_id, PERM_TRANSACTIONS_MANAGE)
    enforce_facility_scope(access, facility_id)
    org = _resolve_org(org_id)
    facility = _resolve_facility(org, facility_id)
    data = {
        "transaction_type": transaction_type,
        "reference_number": reference_number,
        "notes": notes,
        "picks": picks,
        "drops": drops,
    }
    return _txn(create_transaction(org, facility, data, user=uid))


@sync_to_async
def wms_execute_transaction(org_id: str, transaction_id: str, uid: str = "") -> dict:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_TRANSACTIONS_MANAGE
    from app.operations.services import execute_transaction, get_transaction
    access = _check(uid, org_id, PERM_TRANSACTIONS_MANAGE)
    org = _resolve_org(org_id)
    txn = get_transaction(org, transaction_id)
    enforce_facility_scope(access, txn.facility.code)
    return _txn(execute_transaction(txn))


@sync_to_async
def wms_cancel_transaction(org_id: str, transaction_id: str, uid: str = "") -> dict:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_TRANSACTIONS_MANAGE
    from app.operations.services import cancel_transaction, get_transaction
    access = _check(uid, org_id, PERM_TRANSACTIONS_MANAGE)
    org = _resolve_org(org_id)
    txn = get_transaction(org, transaction_id)
    enforce_facility_scope(access, txn.facility.code)
    return _txn(cancel_transaction(txn))


@sync_to_async
def wms_move_inventory(
    org_id: str,
    facility_id: str,
    sku_code: str,
    source_entity_code: str,
    dest_entity_code: str,
    quantity: str,
    source_entity_type: str = "LOCATION",
    dest_entity_type: str = "LOCATION",
    batch_number: str = "",
    reference_number: str = "",
    uid: str = "",
) -> dict:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_OPERATIONS_EXECUTE
    from app.operations.services import create_and_execute_move
    access = _check(uid, org_id, PERM_OPERATIONS_EXECUTE)
    enforce_facility_scope(access, facility_id)
    org = _resolve_org(org_id)
    facility = _resolve_facility(org, facility_id)
    data = {
        "sku_code": sku_code,
        "source_entity_type": source_entity_type,
        "source_entity_code": source_entity_code,
        "dest_entity_type": dest_entity_type,
        "dest_entity_code": dest_entity_code,
        "quantity": Decimal(quantity),
        "batch_number": batch_number,
        "reference_number": reference_number,
    }
    return _txn(create_and_execute_move(org, facility, data, user=uid))


@sync_to_async
def wms_create_grn(
    org_id: str,
    facility_id: str,
    items: list[dict],
    reference_number: str = "",
    notes: str = "",
    uid: str = "",
) -> dict:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_OPERATIONS_EXECUTE
    from app.operations.services import create_and_execute_grn
    access = _check(uid, org_id, PERM_OPERATIONS_EXECUTE)
    enforce_facility_scope(access, facility_id)
    org = _resolve_org(org_id)
    facility = _resolve_facility(org, facility_id)
    normalized = [
        {**item, "quantity": Decimal(str(item["quantity"]))}
        for item in items
    ]
    data = {"items": normalized, "reference_number": reference_number, "notes": notes}
    return _txn(create_and_execute_grn(org, facility, data, user=uid))


@sync_to_async
def wms_putaway(
    org_id: str,
    facility_id: str,
    sku_code: str,
    dest_entity_code: str,
    quantity: str,
    source_entity_code: str = "PRE_PUTAWAY",
    source_entity_type: str = "ZONE",
    dest_entity_type: str = "LOCATION",
    batch_number: str = "",
    reference_number: str = "",
    uid: str = "",
) -> dict:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_OPERATIONS_EXECUTE
    from app.operations.services import create_and_execute_putaway
    access = _check(uid, org_id, PERM_OPERATIONS_EXECUTE)
    enforce_facility_scope(access, facility_id)
    org = _resolve_org(org_id)
    facility = _resolve_facility(org, facility_id)
    data = {
        "sku_code": sku_code,
        "source_entity_type": source_entity_type,
        "source_entity_code": source_entity_code,
        "dest_entity_type": dest_entity_type,
        "dest_entity_code": dest_entity_code,
        "quantity": Decimal(quantity),
        "batch_number": batch_number,
        "reference_number": reference_number,
    }
    return _txn(create_and_execute_putaway(org, facility, data, user=uid))


async def wms_semantic_search(
    org_id: str,
    query: str,
    content_types: list[str] | None = None,
    limit: int = 5,
    uid: str = "",
) -> list[dict]:
    """Semantic similarity search over embedded WMS data."""
    from app.auth.permissions import PERM_INVENTORY_READ
    from app.ai.embeddings import embed_text, semantic_search
    _check(uid, org_id, PERM_INVENTORY_READ)
    types = content_types or ["transaction", "sku", "message", "knowledge"]
    vector = await embed_text(query)
    results = await sync_to_async(semantic_search)(vector, org_id, types, min(limit, 10))
    return results


@sync_to_async
def wms_order_pick(
    org_id: str,
    facility_id: str,
    sku_code: str,
    source_entity_code: str,
    dest_entity_code: str,
    quantity: str,
    source_entity_type: str = "LOCATION",
    dest_entity_type: str = "INVOICE",
    batch_number: str = "",
    reference_number: str = "",
    uid: str = "",
) -> dict:
    from app.auth.authorization import enforce_facility_scope
    from app.auth.permissions import PERM_OPERATIONS_EXECUTE
    from app.operations.services import create_and_execute_order_pick
    access = _check(uid, org_id, PERM_OPERATIONS_EXECUTE)
    enforce_facility_scope(access, facility_id)
    org = _resolve_org(org_id)
    facility = _resolve_facility(org, facility_id)
    data = {
        "sku_code": sku_code,
        "source_entity_type": source_entity_type,
        "source_entity_code": source_entity_code,
        "dest_entity_type": dest_entity_type,
        "dest_entity_code": dest_entity_code,
        "quantity": Decimal(quantity),
        "batch_number": batch_number,
        "reference_number": reference_number,
    }
    return _txn(create_and_execute_order_pick(org, facility, data, user=uid))
