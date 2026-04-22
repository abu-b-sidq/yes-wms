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
    created_by: str = ""
    performed_by: str = ""


class DropOut(Schema):
    id: str
    sku_code: str
    dest_entity_type: str
    dest_entity_code: str
    quantity: Decimal
    batch_number: str
    paired_pick_id: str | None = None
    created_by: str = ""
    performed_by: str = ""


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
    created_by: str = ""


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


class VirtualWarehouseFacilityOut(Schema):
    code: str
    name: str
    warehouse_key: str


class VirtualWarehouseAreaOut(Schema):
    key: str
    label: str
    kind: str
    x: int
    y: int
    w: int
    h: int


class VirtualWarehouseSceneOut(Schema):
    width: int
    height: int
    areas: list[VirtualWarehouseAreaOut] = []


class VirtualWarehouseZoneOut(Schema):
    code: str
    name: str
    kind: str
    label: str
    x: int
    y: int
    w: int
    h: int


class VirtualWarehouseStockItemOut(Schema):
    sku_code: str
    sku_name: str
    batch_number: str
    quantity_on_hand: Decimal
    quantity_available: Decimal
    quantity_reserved: Decimal


class VirtualWarehouseTaskSummaryOut(Schema):
    id: str
    task_type: str
    task_status: str
    transaction_id: str
    transaction_type: str
    reference_number: str
    sku_code: str
    sku_name: str
    quantity: Decimal
    counterpart_entity_code: str | None = None
    assigned_to_name: str | None = None
    picked_by_name: str | None = None
    task_started_at: datetime | None = None
    task_completed_at: datetime | None = None


class VirtualWarehouseLocationOut(Schema):
    code: str
    name: str
    zone_code: str
    kind: str
    x: int
    y: int
    w: int
    h: int
    rotation: int = 0
    quantity_on_hand: Decimal
    quantity_available: Decimal
    quantity_reserved: Decimal
    stock_items: list[VirtualWarehouseStockItemOut] = []
    active_tasks: list[VirtualWarehouseTaskSummaryOut] = []
    worker_ids: list[str] = []


class VirtualWarehouseWorkerOut(Schema):
    id: str
    user_id: str
    display_name: str
    state: str
    x: int
    y: int
    task_id: str
    task_type: str
    task_status: str
    sku_code: str
    sku_name: str
    quantity: Decimal
    source_entity_type: str | None = None
    source_entity_code: str | None = None
    dest_entity_type: str | None = None
    dest_entity_code: str | None = None
    assigned_at: datetime | None = None
    task_started_at: datetime | None = None
    task_completed_at: datetime | None = None


class VirtualWarehouseTaskLinkOut(Schema):
    id: str
    state: str
    worker_id: str
    worker_name: str
    sku_code: str
    quantity: Decimal
    source_entity_type: str
    source_entity_code: str
    dest_entity_type: str
    dest_entity_code: str
    source_x: int
    source_y: int
    dest_x: int
    dest_y: int


class VirtualWarehouseSummaryOut(Schema):
    location_quantity: Decimal
    user_quantity: Decimal
    workers_active: int
    workers_carrying: int
    locations_with_stock: int
    unplaced_location_count: int


class VirtualWarehouseUnplacedLocationOut(Schema):
    code: str
    name: str
    zone_code: str


class VirtualWarehouseOut(Schema):
    facility: VirtualWarehouseFacilityOut
    scene: VirtualWarehouseSceneOut
    zones: list[VirtualWarehouseZoneOut] = []
    locations: list[VirtualWarehouseLocationOut] = []
    workers: list[VirtualWarehouseWorkerOut] = []
    task_links: list[VirtualWarehouseTaskLinkOut] = []
    summary: VirtualWarehouseSummaryOut
    unplaced_locations: list[VirtualWarehouseUnplacedLocationOut] = []
