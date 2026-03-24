from __future__ import annotations

from decimal import Decimal

from django.db.models import F

from app.core.enums import LedgerEntryType
from app.core.exceptions import InsufficientInventoryError
from app.inventory.models import InventoryBalance, InventoryLedger
from app.masters.models import Facility, Organization, SKU
from app.operations.models import Drop, Pick, Transaction


def debit_balance(
    org: Organization,
    facility: Facility,
    sku: SKU,
    entity_type: str,
    entity_code: str,
    quantity: Decimal,
    batch_number: str,
    transaction: Transaction,
    pick: Pick | None = None,
) -> InventoryLedger:
    """Debit (subtract) from inventory balance. Used during pick execution."""
    balance, _ = InventoryBalance.objects.select_for_update().get_or_create(
        org=org,
        facility=facility,
        sku=sku,
        entity_type=entity_type,
        entity_code=entity_code,
        batch_number=batch_number,
        defaults={"quantity_on_hand": 0, "quantity_reserved": 0, "quantity_available": 0},
    )

    if balance.quantity_available < quantity:
        raise InsufficientInventoryError(
            f"Insufficient inventory for {sku.code} at {entity_type}:{entity_code}. "
            f"Available: {balance.quantity_available}, Requested: {quantity}",
            details={
                "sku_code": sku.code,
                "entity_type": entity_type,
                "entity_code": entity_code,
                "available": str(balance.quantity_available),
                "requested": str(quantity),
            },
        )

    balance.quantity_on_hand = F("quantity_on_hand") - quantity
    balance.quantity_available = F("quantity_available") - quantity
    balance.save(update_fields=["quantity_on_hand", "quantity_available", "updated_at"])
    balance.refresh_from_db()

    return InventoryLedger.objects.create(
        org=org,
        facility=facility,
        sku=sku,
        transaction=transaction,
        entry_type=LedgerEntryType.PICK,
        entity_type=entity_type,
        entity_code=entity_code,
        batch_number=batch_number,
        quantity=-quantity,
        balance_after=balance.quantity_on_hand,
        pick=pick,
    )


def credit_balance(
    org: Organization,
    facility: Facility,
    sku: SKU,
    entity_type: str,
    entity_code: str,
    quantity: Decimal,
    batch_number: str,
    transaction: Transaction,
    drop: Drop | None = None,
) -> InventoryLedger:
    """Credit (add) to inventory balance. Used during drop execution."""
    balance, _ = InventoryBalance.objects.select_for_update().get_or_create(
        org=org,
        facility=facility,
        sku=sku,
        entity_type=entity_type,
        entity_code=entity_code,
        batch_number=batch_number,
        defaults={"quantity_on_hand": 0, "quantity_reserved": 0, "quantity_available": 0},
    )

    balance.quantity_on_hand = F("quantity_on_hand") + quantity
    balance.quantity_available = F("quantity_available") + quantity
    balance.save(update_fields=["quantity_on_hand", "quantity_available", "updated_at"])
    balance.refresh_from_db()

    return InventoryLedger.objects.create(
        org=org,
        facility=facility,
        sku=sku,
        transaction=transaction,
        entry_type=LedgerEntryType.DROP,
        entity_type=entity_type,
        entity_code=entity_code,
        batch_number=batch_number,
        quantity=quantity,
        balance_after=balance.quantity_on_hand,
        drop=drop,
    )


def get_balances(
    org: Organization,
    facility: Facility | None = None,
    sku_code: str | None = None,
    entity_type: str | None = None,
    entity_code: str | None = None,
) -> list[InventoryBalance]:
    qs = InventoryBalance.objects.filter(org=org).select_related("facility", "sku")
    if facility:
        qs = qs.filter(facility=facility)
    if sku_code:
        qs = qs.filter(sku__code=sku_code)
    if entity_type:
        qs = qs.filter(entity_type=entity_type)
    if entity_code:
        qs = qs.filter(entity_code=entity_code)
    return list(qs.order_by("sku__code", "entity_type", "entity_code")[:200])


def get_balances_by_location(
    org: Organization, facility: Facility, location_code: str
) -> list[InventoryBalance]:
    return list(
        InventoryBalance.objects.filter(
            org=org,
            facility=facility,
            entity_type="LOCATION",
            entity_code=location_code,
        )
        .select_related("sku")
        .order_by("sku__code")
    )


def get_balances_by_sku(
    org: Organization, facility: Facility, sku_code: str
) -> list[InventoryBalance]:
    return list(
        InventoryBalance.objects.filter(
            org=org,
            facility=facility,
            sku__code=sku_code,
        )
        .select_related("sku")
        .order_by("entity_type", "entity_code")
    )


def get_ledger(
    org: Organization,
    facility: Facility | None = None,
    sku_code: str | None = None,
    transaction_id: str | None = None,
) -> list[InventoryLedger]:
    qs = InventoryLedger.objects.filter(org=org).select_related(
        "sku", "transaction", "facility"
    )
    if facility:
        qs = qs.filter(facility=facility)
    if sku_code:
        qs = qs.filter(sku__code=sku_code)
    if transaction_id:
        qs = qs.filter(transaction_id=transaction_id)
    return list(qs.order_by("-created_at")[:200])
