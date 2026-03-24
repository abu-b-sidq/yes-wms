from datetime import datetime
from decimal import Decimal

from ninja import Schema


class BalanceOut(Schema):
    id: str
    facility_code: str
    sku_code: str
    entity_type: str
    entity_code: str
    batch_number: str
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal
    updated_at: datetime


class LedgerEntryOut(Schema):
    id: str
    facility_code: str
    sku_code: str
    transaction_id: str
    entry_type: str
    entity_type: str
    entity_code: str
    batch_number: str
    quantity: Decimal
    balance_after: Decimal
    created_at: datetime
