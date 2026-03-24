from __future__ import annotations

from ninja import Router

from app.core.openapi import protected_openapi_extra
from app.core.response import success_response
from app.core.tenant import resolve_request_tenant
from app.operations import schemas, services

router = Router(tags=["operations"])
ORG_PROTECTED = protected_openapi_extra()
ORG_WITH_OPTIONAL_FACILITY = protected_openapi_extra(include_facility=True)
ORG_WITH_REQUIRED_FACILITY = protected_openapi_extra(require_facility=True)


@router.post(
    "/transactions",
    summary="Create transaction",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def create_transaction(request, payload: schemas.TransactionCreateIn):
    org, facility = resolve_request_tenant(request, require_facility=True)
    user = _get_user(request)
    txn = services.create_transaction(org, facility, payload.dict(), user=user)
    return success_response(request, data=_txn_out(txn))


@router.get(
    "/transactions",
    summary="List transactions",
    openapi_extra=ORG_WITH_OPTIONAL_FACILITY,
)
def list_transactions(
    request,
    transaction_type: str | None = None,
    status: str | None = None,
):
    org, facility = resolve_request_tenant(request)
    txns = services.list_transactions(
        org, facility=facility, transaction_type=transaction_type, status=status
    )
    return success_response(request, data=[_txn_out(t) for t in txns])


@router.get(
    "/transactions/{txn_id}",
    summary="Get transaction",
    openapi_extra=ORG_PROTECTED,
)
def get_transaction(request, txn_id: str):
    org, _ = resolve_request_tenant(request)
    txn = services.get_transaction(org, txn_id)
    return success_response(request, data=_txn_out(txn))


@router.post(
    "/transactions/{txn_id}/execute",
    summary="Execute transaction",
    openapi_extra=ORG_PROTECTED,
)
def execute_transaction(request, txn_id: str):
    org, _ = resolve_request_tenant(request)
    txn = services.get_transaction(org, txn_id)
    txn = services.execute_transaction(txn)
    return success_response(request, data=_txn_out(txn))


@router.post(
    "/transactions/{txn_id}/cancel",
    summary="Cancel transaction",
    openapi_extra=ORG_PROTECTED,
)
def cancel_transaction(request, txn_id: str):
    org, _ = resolve_request_tenant(request)
    txn = services.get_transaction(org, txn_id)
    txn = services.cancel_transaction(txn)
    return success_response(request, data=_txn_out(txn))


# --- Convenience endpoints ---

@router.post(
    "/move",
    summary="Move inventory (create + execute)",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def move(request, payload: schemas.MoveIn):
    org, facility = resolve_request_tenant(request, require_facility=True)
    user = _get_user(request)
    txn = services.create_and_execute_move(org, facility, payload.dict(), user=user)
    return success_response(request, data=_txn_out(txn))


@router.post(
    "/grn",
    summary="Goods Received Note (create + execute)",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def grn(request, payload: schemas.GRNIn):
    org, facility = resolve_request_tenant(request, require_facility=True)
    user = _get_user(request)
    txn = services.create_and_execute_grn(org, facility, payload.dict(), user=user)
    return success_response(request, data=_txn_out(txn))


@router.post(
    "/putaway",
    summary="Putaway (create + execute)",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def putaway(request, payload: schemas.PutawayIn):
    org, facility = resolve_request_tenant(request, require_facility=True)
    user = _get_user(request)
    txn = services.create_and_execute_putaway(org, facility, payload.dict(), user=user)
    return success_response(request, data=_txn_out(txn))


@router.post(
    "/order-pick",
    summary="Order pick (create + execute)",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def order_pick(request, payload: schemas.OrderPickIn):
    org, facility = resolve_request_tenant(request, require_facility=True)
    user = _get_user(request)
    txn = services.create_and_execute_order_pick(org, facility, payload.dict(), user=user)
    return success_response(request, data=_txn_out(txn))


# --- Helpers ---

def _get_user(request) -> str:
    auth = getattr(request, "auth_context", None)
    if auth and auth.uid:
        return auth.uid
    if auth and auth.client_name:
        return auth.client_name
    return ""


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
    ).dict()
