from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ninja import Schema


class PickIn(Schema):
    sku_code: str
    source_entity_type: str
    source_entity_code: str
    quantity: Decimal
    batch_number: str = ""


class DropIn(Schema):
    sku_code: str
    dest_entity_type: str
    dest_entity_code: str
    quantity: Decimal
    batch_number: str = ""


class TransactionCreateIn(Schema):
    transaction_type: str
    reference_number: str = ""
    notes: str = ""
    picks: list[PickIn] = []
    drops: list[DropIn] = []


class TransactionExecuteIn(Schema):
    """Optional: provide additional picks/drops at execution time."""
    picks: list[PickIn] = []
    drops: list[DropIn] = []


class PickOut(Schema):
    id: str
    sku_code: str
    source_entity_type: str
    source_entity_code: str
    quantity: Decimal
    batch_number: str


class DropOut(Schema):
    id: str
    sku_code: str
    dest_entity_type: str
    dest_entity_code: str
    quantity: Decimal
    batch_number: str
    paired_pick_id: str | None = None


class TransactionOut(Schema):
    id: str
    transaction_type: str
    status: str
    reference_number: str
    notes: str
    picks: list[PickOut] = []
    drops: list[DropOut] = []
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    document_url: str = ""


# --- Convenience endpoints ---

class MoveIn(Schema):
    sku_code: str
    source_entity_type: str = "LOCATION"
    source_entity_code: str
    dest_entity_type: str = "LOCATION"
    dest_entity_code: str
    quantity: Decimal
    batch_number: str = ""
    reference_number: str = ""
    notes: str = ""


class GRNItemIn(Schema):
    sku_code: str
    quantity: Decimal
    batch_number: str = ""
    dest_entity_type: str = "ZONE"
    dest_entity_code: str = "PRE_PUTAWAY"


class GRNIn(Schema):
    items: list[GRNItemIn]
    reference_number: str = ""
    notes: str = ""


class PutawayIn(Schema):
    sku_code: str
    source_entity_type: str = "ZONE"
    source_entity_code: str = "PRE_PUTAWAY"
    dest_entity_type: str = "LOCATION"
    dest_entity_code: str
    quantity: Decimal
    batch_number: str = ""
    reference_number: str = ""
    notes: str = ""


class OrderPickIn(Schema):
    sku_code: str
    source_entity_type: str = "LOCATION"
    source_entity_code: str
    dest_entity_type: str = "INVOICE"
    dest_entity_code: str
    quantity: Decimal
    batch_number: str = ""
    reference_number: str = ""
    notes: str = ""
