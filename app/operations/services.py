from __future__ import annotations

import logging
from decimal import Decimal

from django.db import transaction as db_transaction

from app.core.enums import EntityType, LedgerEntryType, TransactionStatus, TransactionType
from app.core.exceptions import InsufficientInventoryError, ValidationError
from app.masters.models import Facility, Location, Organization
from app.masters.services import get_sku
from app.operations.models import Drop, Pick, Transaction
from app.operations.state_machine import transition
from app.operations.validators import (
    validate_drop_data,
    validate_pick_data,
    validate_transaction_shape,
)

logger = logging.getLogger("app.operations")


def create_transaction(
    org: Organization,
    facility: Facility,
    data: dict,
    user: str = "",
) -> Transaction:
    picks_data = data.pop("picks", [])
    drops_data = data.pop("drops", [])

    for p in picks_data:
        validate_pick_data(p)
    for d in drops_data:
        validate_drop_data(d)

    validate_transaction_shape(data["transaction_type"], picks_data, drops_data)

    with db_transaction.atomic():
        txn = Transaction.objects.create(
            org=org,
            facility=facility,
            created_by=user,
            updated_by=user,
            **data,
        )
        _create_picks(txn, org, picks_data)
        _create_drops(txn, org, drops_data)

    txn = Transaction.objects.select_related("facility").prefetch_related(
        "picks__sku", "drops__sku", "drops__paired_pick"
    ).get(pk=txn.pk)

    # Notify workers of new pick tasks
    _notify_new_pick_tasks(txn)

    return txn


def execute_transaction(txn: Transaction) -> Transaction:
    from app.inventory.services import credit_balance, debit_balance

    with db_transaction.atomic():
        transition(txn, TransactionStatus.IN_PROGRESS)

        picks = list(txn.picks.select_related("sku").all())
        drops = list(txn.drops.select_related("sku").all())

        for pick in picks:
            debit_balance(
                org=txn.org,
                facility=txn.facility,
                sku=pick.sku,
                entity_type=pick.source_entity_type,
                entity_code=pick.source_entity_code,
                quantity=pick.quantity,
                batch_number=pick.batch_number,
                transaction=txn,
                pick=pick,
            )

        for drop in drops:
            credit_balance(
                org=txn.org,
                facility=txn.facility,
                sku=drop.sku,
                entity_type=drop.dest_entity_type,
                entity_code=drop.dest_entity_code,
                quantity=drop.quantity,
                batch_number=drop.batch_number,
                transaction=txn,
                drop=drop,
            )

        transition(txn, TransactionStatus.COMPLETED)

    txn.refresh_from_db()

    from app.documents.services import generate_and_store_document
    url = generate_and_store_document(txn)
    if url:
        txn.document_url = url
        txn.save(update_fields=["document_url", "updated_at"])

    return Transaction.objects.select_related("facility").prefetch_related(
        "picks__sku", "drops__sku", "drops__paired_pick"
    ).get(pk=txn.pk)


def cancel_transaction(txn: Transaction) -> Transaction:
    transition(txn, TransactionStatus.CANCELLED)
    return txn


def get_transaction(org: Organization, txn_id: str) -> Transaction:
    from app.core.exceptions import EntityNotFoundError

    try:
        return Transaction.objects.prefetch_related(
            "picks__sku", "drops__sku", "drops__paired_pick"
        ).select_related("facility").get(org=org, pk=txn_id)
    except Transaction.DoesNotExist:
        raise EntityNotFoundError(f"Transaction '{txn_id}' not found.")


def list_transactions(
    org: Organization,
    facility: Facility | None = None,
    transaction_type: str | None = None,
    status: str | None = None,
) -> list[Transaction]:
    qs = Transaction.objects.filter(org=org).select_related("facility").prefetch_related(
        "picks__sku", "drops__sku"
    )
    if facility:
        qs = qs.filter(facility=facility)
    if transaction_type:
        qs = qs.filter(transaction_type=transaction_type)
    if status:
        qs = qs.filter(status=status)
    return list(qs.order_by("-created_at")[:100])


def create_and_execute_move(
    org: Organization, facility: Facility, data: dict, user: str = ""
) -> Transaction:
    txn_data = {
        "transaction_type": TransactionType.MOVE,
        "reference_number": data.get("reference_number", ""),
        "notes": data.get("notes", ""),
        "picks": [
            {
                "sku_code": data["sku_code"],
                "source_entity_type": data.get("source_entity_type", EntityType.LOCATION),
                "source_entity_code": data["source_entity_code"],
                "quantity": data["quantity"],
                "batch_number": data.get("batch_number", ""),
            }
        ],
        "drops": [
            {
                "sku_code": data["sku_code"],
                "dest_entity_type": data.get("dest_entity_type", EntityType.LOCATION),
                "dest_entity_code": data["dest_entity_code"],
                "quantity": data["quantity"],
                "batch_number": data.get("batch_number", ""),
            }
        ],
    }
    txn = create_transaction(org, facility, txn_data, user=user)
    return execute_transaction(txn)


def create_and_execute_grn(
    org: Organization, facility: Facility, data: dict, user: str = ""
) -> Transaction:
    drops = []
    for item in data["items"]:
        drops.append(
            {
                "sku_code": item["sku_code"],
                "dest_entity_type": item.get("dest_entity_type", EntityType.ZONE),
                "dest_entity_code": item.get("dest_entity_code", "PRE_PUTAWAY"),
                "quantity": item["quantity"],
                "batch_number": item.get("batch_number", ""),
            }
        )
    txn_data = {
        "transaction_type": TransactionType.GRN,
        "reference_number": data.get("reference_number", ""),
        "notes": data.get("notes", ""),
        "picks": [],
        "drops": drops,
    }
    txn = create_transaction(org, facility, txn_data, user=user)
    return execute_transaction(txn)


def create_and_execute_putaway(
    org: Organization, facility: Facility, data: dict, user: str = ""
) -> Transaction:
    txn_data = {
        "transaction_type": TransactionType.PUTAWAY,
        "reference_number": data.get("reference_number", ""),
        "notes": data.get("notes", ""),
        "picks": [
            {
                "sku_code": data["sku_code"],
                "source_entity_type": data.get("source_entity_type", EntityType.ZONE),
                "source_entity_code": data.get("source_entity_code", "PRE_PUTAWAY"),
                "quantity": data["quantity"],
                "batch_number": data.get("batch_number", ""),
            }
        ],
        "drops": [
            {
                "sku_code": data["sku_code"],
                "dest_entity_type": data.get("dest_entity_type", EntityType.LOCATION),
                "dest_entity_code": data["dest_entity_code"],
                "quantity": data["quantity"],
                "batch_number": data.get("batch_number", ""),
            }
        ],
    }
    txn = create_transaction(org, facility, txn_data, user=user)
    return execute_transaction(txn)


def create_and_execute_order_pick(
    org: Organization, facility: Facility, data: dict, user: str = ""
) -> Transaction:
    txn_data = {
        "transaction_type": TransactionType.ORDER_PICK,
        "reference_number": data.get("reference_number", ""),
        "notes": data.get("notes", ""),
        "picks": [
            {
                "sku_code": data["sku_code"],
                "source_entity_type": data.get("source_entity_type", EntityType.LOCATION),
                "source_entity_code": data["source_entity_code"],
                "quantity": data["quantity"],
                "batch_number": data.get("batch_number", ""),
            }
        ],
        "drops": [
            {
                "sku_code": data["sku_code"],
                "dest_entity_type": data.get("dest_entity_type", EntityType.INVOICE),
                "dest_entity_code": data["dest_entity_code"],
                "quantity": data["quantity"],
                "batch_number": data.get("batch_number", ""),
            }
        ],
    }
    txn = create_transaction(org, facility, txn_data, user=user)
    return execute_transaction(txn)


# --- Internal helpers ---

def _create_picks(txn: Transaction, org: Organization, picks_data: list[dict]) -> list[Pick]:
    picks = []
    for p in picks_data:
        sku = get_sku(org, p["sku_code"])
        source_location = None
        if p["source_entity_type"] == EntityType.LOCATION:
            source_location = Location.objects.filter(
                org=org, code=p["source_entity_code"]
            ).first()
        pick = Pick.objects.create(
            org=org,
            transaction=txn,
            sku=sku,
            source_entity_type=p["source_entity_type"],
            source_entity_code=p["source_entity_code"],
            source_location=source_location,
            quantity=Decimal(str(p["quantity"])),
            batch_number=p.get("batch_number", ""),
            created_by=txn.created_by,
            updated_by=txn.created_by,
        )
        picks.append(pick)
    return picks


def _create_drops(txn: Transaction, org: Organization, drops_data: list[dict]) -> list[Drop]:
    drops = []
    for i, d in enumerate(drops_data):
        sku = get_sku(org, d["sku_code"])
        dest_location = None
        if d["dest_entity_type"] == EntityType.LOCATION:
            dest_location = Location.objects.filter(
                org=org, code=d["dest_entity_code"]
            ).first()
        # Pair with pick if same index exists
        paired_pick = None
        picks = list(txn.picks.all())
        if i < len(picks):
            paired_pick = picks[i]
        drop = Drop.objects.create(
            org=org,
            transaction=txn,
            sku=sku,
            dest_entity_type=d["dest_entity_type"],
            dest_entity_code=d["dest_entity_code"],
            dest_location=dest_location,
            quantity=Decimal(str(d["quantity"])),
            batch_number=d.get("batch_number", ""),
            paired_pick=paired_pick,
            created_by=txn.created_by,
            updated_by=txn.created_by,
        )
        drops.append(drop)
    return drops


def _notify_new_pick_tasks(txn: Transaction) -> None:
    """Send push + WebSocket notifications for new pick tasks."""
    try:
        from app.notifications.fcm_service import notify_new_pick_task
        from app.notifications.websocket import broadcast_to_facility

        facility_id = str(txn.facility_id)
        picks = list(txn.picks.select_related("sku").all())

        for pick in picks:
            notify_new_pick_task(facility_id, pick)

        if picks:
            broadcast_to_facility(facility_id, {
                "type": "new_task_available",
                "transaction_id": str(txn.pk),
                "pick_count": len(picks),
            })
    except Exception:
        logger.debug("Failed to send new task notifications for txn %s", txn.pk)
