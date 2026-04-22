from __future__ import annotations

from collections import defaultdict
import logging
from decimal import Decimal

from django.db import transaction as db_transaction

from app.core.enums import EntityType, LedgerEntryType, TaskStatus, TransactionStatus, TransactionType
from app.core.exceptions import InsufficientInventoryError, ValidationError
from app.inventory.models import InventoryBalance
from app.masters.models import Facility, FacilityLocation, FacilityZone, Location, Organization
from app.masters.services import get_sku
from app.operations.models import Drop, Pick, Transaction
from app.operations.state_machine import transition
from app.operations.validators import (
    validate_drop_data,
    validate_pick_data,
    validate_transaction_shape,
)

logger = logging.getLogger("app.operations")

VIRTUAL_WAREHOUSE_WIDTH = 1600
VIRTUAL_WAREHOUSE_HEIGHT = 900
DEFAULT_LOCATION_WIDTH = 52
DEFAULT_LOCATION_HEIGHT = 28
DEFAULT_ZONE_WIDTH = 240
DEFAULT_ZONE_HEIGHT = 180
FIXED_VIRTUAL_WAREHOUSE_AREAS = {
    "receiving": {
        "key": "receiving",
        "label": "Receiving",
        "kind": "receiving",
        "x": 80,
        "y": 680,
        "w": 240,
        "h": 150,
    },
    "dispatch": {
        "key": "dispatch",
        "label": "Dispatch",
        "kind": "dispatch",
        "x": 1270,
        "y": 680,
        "w": 250,
        "h": 150,
    },
    "service": {
        "key": "service",
        "label": "Service",
        "kind": "service",
        "x": 1240,
        "y": 120,
        "w": 240,
        "h": 130,
    },
}


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

    # Notify workers of new available tasks.
    _notify_new_tasks(txn)

    return txn


def execute_transaction(txn: Transaction, user: str = "") -> Transaction:
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

        if user:
            Pick.objects.filter(transaction=txn).update(performed_by=user, updated_by=user)
            Drop.objects.filter(transaction=txn).update(performed_by=user, updated_by=user)
            txn.updated_by = user
            txn.save(update_fields=["updated_by", "updated_at"])

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
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    size: int = 25,
) -> tuple[list[Transaction], int]:
    qs = Transaction.objects.filter(org=org).select_related("facility").prefetch_related(
        "picks__sku", "drops__sku"
    )
    if facility:
        qs = qs.filter(facility=facility)
    if transaction_type:
        qs = qs.filter(transaction_type=transaction_type)
    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__lte=date_to)
    qs = qs.order_by("-created_at")
    total = qs.count()
    offset = (page - 1) * size
    return list(qs[offset:offset + size]), total


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
    return execute_transaction(txn, user=user)


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
    return execute_transaction(txn, user=user)


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
    return execute_transaction(txn, user=user)


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
    return execute_transaction(txn, user=user)


def get_virtual_warehouse(org: Organization, facility: Facility) -> dict:
    zone_mappings = list(
        FacilityZone.objects.filter(facility=facility, is_active=True)
        .select_related("zone")
        .order_by("zone__code")
    )
    location_mappings = list(
        FacilityLocation.objects.filter(facility=facility, is_active=True)
        .select_related("location", "location__zone")
        .order_by("location__code")
    )
    balances = list(
        InventoryBalance.objects.filter(
            org=org,
            facility=facility,
            entity_type=EntityType.LOCATION,
        )
        .select_related("sku")
        .order_by("entity_code", "sku__code", "batch_number")
    )
    active_picks = list(
        Pick.objects.filter(
            org=org,
            transaction__facility=facility,
            task_status__in=[TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS],
            assigned_to__isnull=False,
        )
        .select_related("assigned_to", "sku", "transaction")
        .order_by("assigned_at", "created_at")
    )
    active_drops = list(
        Drop.objects.filter(
            org=org,
            transaction__facility=facility,
            task_status__in=[TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS],
        )
        .select_related("assigned_to", "sku", "transaction", "paired_pick", "paired_pick__assigned_to")
        .order_by("assigned_at", "created_at")
    )

    location_balance_map: dict[str, list[InventoryBalance]] = defaultdict(list)
    for balance in balances:
        location_balance_map[balance.entity_code].append(balance)

    scene = {
        "width": VIRTUAL_WAREHOUSE_WIDTH,
        "height": VIRTUAL_WAREHOUSE_HEIGHT,
        "areas": list(FIXED_VIRTUAL_WAREHOUSE_AREAS.values()),
    }

    zone_scene_by_code: dict[str, dict] = {}
    zones: list[dict] = []
    for mapping in zone_mappings:
        layout = _virtual_warehouse_override(mapping.overrides)
        if not layout:
            continue
        zone = {
            "code": mapping.zone.code,
            "name": mapping.zone.name,
            "kind": layout.get("kind", "storage"),
            "label": layout.get("label", mapping.zone.name),
            "x": _coerce_int(layout.get("x"), 0),
            "y": _coerce_int(layout.get("y"), 0),
            "w": _coerce_int(layout.get("w"), DEFAULT_ZONE_WIDTH),
            "h": _coerce_int(layout.get("h"), DEFAULT_ZONE_HEIGHT),
        }
        zone_scene_by_code[mapping.zone.code] = zone
        zones.append(zone)

    location_scene_by_code: dict[str, dict] = {}
    unplaced_locations: list[dict] = []
    locations: list[dict] = []
    locations_with_stock = 0
    location_quantity = Decimal("0")

    for mapping in location_mappings:
        layout = _virtual_warehouse_override(mapping.overrides)
        if not layout:
            unplaced_locations.append({
                "code": mapping.location.code,
                "name": mapping.location.name,
                "zone_code": mapping.location.zone.code,
            })
            continue
        if layout.get("hidden") is True:
            continue

        stock_items = []
        quantity_on_hand = Decimal("0")
        quantity_available = Decimal("0")
        quantity_reserved = Decimal("0")
        for balance in location_balance_map.get(mapping.location.code, []):
            quantity_on_hand += balance.quantity_on_hand
            quantity_available += balance.quantity_available
            quantity_reserved += balance.quantity_reserved
            stock_items.append({
                "sku_code": balance.sku.code,
                "sku_name": balance.sku.name,
                "batch_number": balance.batch_number,
                "quantity_on_hand": balance.quantity_on_hand,
                "quantity_available": balance.quantity_available,
                "quantity_reserved": balance.quantity_reserved,
            })

        if quantity_on_hand > 0:
            locations_with_stock += 1
        location_quantity += quantity_on_hand

        location = {
            "code": mapping.location.code,
            "name": mapping.location.name,
            "zone_code": mapping.location.zone.code,
            "kind": layout.get("kind", "rack"),
            "x": _coerce_int(layout.get("x"), 0),
            "y": _coerce_int(layout.get("y"), 0),
            "w": _coerce_int(layout.get("w"), DEFAULT_LOCATION_WIDTH),
            "h": _coerce_int(layout.get("h"), DEFAULT_LOCATION_HEIGHT),
            "rotation": _coerce_int(layout.get("rotation"), 0),
            "quantity_on_hand": quantity_on_hand,
            "quantity_available": quantity_available,
            "quantity_reserved": quantity_reserved,
            "stock_items": stock_items,
            "active_tasks": [],
            "worker_ids": [],
        }
        location_scene_by_code[mapping.location.code] = location
        locations.append(location)

    workers: list[dict] = []
    task_links: list[dict] = []
    user_quantity = Decimal("0")
    carrying_worker_ids: set[str] = set()
    active_worker_ids: set[str] = set()

    for pick in active_picks:
        anchor = _resolve_virtual_anchor(
            pick.source_entity_type,
            pick.source_entity_code,
            location_scene_by_code,
            zone_scene_by_code,
        )
        if anchor is None:
            continue

        worker_name = _display_name(pick.assigned_to)
        worker_id = str(pick.assigned_to_id)
        active_worker_ids.add(worker_id)
        worker = {
            "id": f"pick-{pick.id}",
            "user_id": worker_id,
            "display_name": worker_name,
            "state": "picking",
            "x": anchor["x"],
            "y": anchor["y"],
            "task_id": str(pick.id),
            "task_type": "pick",
            "task_status": pick.task_status,
            "sku_code": pick.sku.code,
            "sku_name": pick.sku.name,
            "quantity": pick.quantity,
            "source_entity_type": pick.source_entity_type,
            "source_entity_code": pick.source_entity_code,
            "dest_entity_type": None,
            "dest_entity_code": None,
            "assigned_at": pick.assigned_at,
            "task_started_at": pick.task_started_at,
            "task_completed_at": pick.task_completed_at,
        }
        workers.append(worker)
        _append_location_task(
            pick.source_entity_code,
            location_scene_by_code,
            {
                "id": str(pick.id),
                "task_type": "pick",
                "task_status": pick.task_status,
                "transaction_id": str(pick.transaction_id),
                "transaction_type": pick.transaction.transaction_type,
                "reference_number": pick.transaction.reference_number,
                "sku_code": pick.sku.code,
                "sku_name": pick.sku.name,
                "quantity": pick.quantity,
                "counterpart_entity_code": None,
                "assigned_to_name": worker_name,
                "picked_by_name": worker_name,
                "task_started_at": pick.task_started_at,
                "task_completed_at": pick.task_completed_at,
            },
            worker_id,
        )

    for drop in active_drops:
        if drop.paired_pick_id and drop.paired_pick and drop.paired_pick.task_status == TaskStatus.COMPLETED:
            source_anchor = _resolve_virtual_anchor(
                drop.paired_pick.source_entity_type,
                drop.paired_pick.source_entity_code,
                location_scene_by_code,
                zone_scene_by_code,
            )
            dest_anchor = _resolve_virtual_anchor(
                drop.dest_entity_type,
                drop.dest_entity_code,
                location_scene_by_code,
                zone_scene_by_code,
            )
            if source_anchor is None or dest_anchor is None:
                continue

            worker_user_id = str(drop.assigned_to_id or drop.paired_pick.assigned_to_id or "unknown")
            worker_name = _display_name(drop.assigned_to or drop.paired_pick.assigned_to)
            active_worker_ids.add(worker_user_id)
            carrying_worker_ids.add(worker_user_id)
            user_quantity += drop.quantity

            state = "dropping" if drop.task_status == TaskStatus.IN_PROGRESS else "carrying"
            worker = {
                "id": f"drop-{drop.id}",
                "user_id": worker_user_id,
                "display_name": worker_name,
                "state": state,
                "x": int((source_anchor["x"] + dest_anchor["x"]) / 2),
                "y": int((source_anchor["y"] + dest_anchor["y"]) / 2),
                "task_id": str(drop.id),
                "task_type": "drop",
                "task_status": drop.task_status,
                "sku_code": drop.sku.code,
                "sku_name": drop.sku.name,
                "quantity": drop.quantity,
                "source_entity_type": drop.paired_pick.source_entity_type,
                "source_entity_code": drop.paired_pick.source_entity_code,
                "dest_entity_type": drop.dest_entity_type,
                "dest_entity_code": drop.dest_entity_code,
                "assigned_at": drop.assigned_at,
                "task_started_at": drop.task_started_at,
                "task_completed_at": drop.paired_pick.task_completed_at,
            }
            workers.append(worker)
            task_links.append({
                "id": str(drop.id),
                "state": state,
                "worker_id": worker["id"],
                "worker_name": worker_name,
                "sku_code": drop.sku.code,
                "quantity": drop.quantity,
                "source_entity_type": drop.paired_pick.source_entity_type,
                "source_entity_code": drop.paired_pick.source_entity_code,
                "dest_entity_type": drop.dest_entity_type,
                "dest_entity_code": drop.dest_entity_code,
                "source_x": source_anchor["x"],
                "source_y": source_anchor["y"],
                "dest_x": dest_anchor["x"],
                "dest_y": dest_anchor["y"],
            })
            _append_location_task(
                drop.paired_pick.source_entity_code,
                location_scene_by_code,
                {
                    "id": str(drop.id),
                    "task_type": "carry",
                    "task_status": drop.task_status,
                    "transaction_id": str(drop.transaction_id),
                    "transaction_type": drop.transaction.transaction_type,
                    "reference_number": drop.transaction.reference_number,
                    "sku_code": drop.sku.code,
                    "sku_name": drop.sku.name,
                    "quantity": drop.quantity,
                    "counterpart_entity_code": drop.dest_entity_code,
                    "assigned_to_name": _display_name(drop.assigned_to),
                    "picked_by_name": _display_name(drop.paired_pick.assigned_to),
                    "task_started_at": drop.task_started_at,
                    "task_completed_at": drop.paired_pick.task_completed_at,
                },
                worker_user_id,
            )
            _append_location_task(
                drop.dest_entity_code,
                location_scene_by_code,
                {
                    "id": str(drop.id),
                    "task_type": "drop",
                    "task_status": drop.task_status,
                    "transaction_id": str(drop.transaction_id),
                    "transaction_type": drop.transaction.transaction_type,
                    "reference_number": drop.transaction.reference_number,
                    "sku_code": drop.sku.code,
                    "sku_name": drop.sku.name,
                    "quantity": drop.quantity,
                    "counterpart_entity_code": drop.paired_pick.source_entity_code,
                    "assigned_to_name": _display_name(drop.assigned_to),
                    "picked_by_name": _display_name(drop.paired_pick.assigned_to),
                    "task_started_at": drop.task_started_at,
                    "task_completed_at": drop.paired_pick.task_completed_at,
                },
                worker_user_id,
            )
            continue

        if not drop.paired_pick_id and drop.assigned_to_id and drop.task_status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
            anchor = _resolve_virtual_anchor(
                drop.dest_entity_type,
                drop.dest_entity_code,
                location_scene_by_code,
                zone_scene_by_code,
            )
            if anchor is None:
                continue

            worker_name = _display_name(drop.assigned_to)
            worker_id = str(drop.assigned_to_id)
            active_worker_ids.add(worker_id)
            worker = {
                "id": f"drop-{drop.id}",
                "user_id": worker_id,
                "display_name": worker_name,
                "state": "dropping",
                "x": anchor["x"],
                "y": anchor["y"],
                "task_id": str(drop.id),
                "task_type": "drop",
                "task_status": drop.task_status,
                "sku_code": drop.sku.code,
                "sku_name": drop.sku.name,
                "quantity": drop.quantity,
                "source_entity_type": None,
                "source_entity_code": None,
                "dest_entity_type": drop.dest_entity_type,
                "dest_entity_code": drop.dest_entity_code,
                "assigned_at": drop.assigned_at,
                "task_started_at": drop.task_started_at,
                "task_completed_at": drop.task_completed_at,
            }
            workers.append(worker)
            _append_location_task(
                drop.dest_entity_code,
                location_scene_by_code,
                {
                    "id": str(drop.id),
                    "task_type": "drop",
                    "task_status": drop.task_status,
                    "transaction_id": str(drop.transaction_id),
                    "transaction_type": drop.transaction.transaction_type,
                    "reference_number": drop.transaction.reference_number,
                    "sku_code": drop.sku.code,
                    "sku_name": drop.sku.name,
                    "quantity": drop.quantity,
                    "counterpart_entity_code": None,
                    "assigned_to_name": worker_name,
                    "picked_by_name": None,
                    "task_started_at": drop.task_started_at,
                    "task_completed_at": drop.task_completed_at,
                },
                worker_id,
            )

    locations.sort(key=lambda item: (item["zone_code"], item["code"]))
    zones.sort(key=lambda item: item["code"])
    workers.sort(key=lambda item: (item["display_name"].lower(), item["id"]))
    task_links.sort(key=lambda item: (item["worker_name"].lower(), item["id"]))
    unplaced_locations.sort(key=lambda item: item["code"])

    return {
        "facility": {
            "code": facility.code,
            "name": facility.name,
            "warehouse_key": facility.warehouse_key,
        },
        "scene": scene,
        "zones": zones,
        "locations": locations,
        "workers": workers,
        "task_links": task_links,
        "summary": {
            "location_quantity": location_quantity,
            "user_quantity": user_quantity,
            "workers_active": len(active_worker_ids),
            "workers_carrying": len(carrying_worker_ids),
            "locations_with_stock": locations_with_stock,
            "unplaced_location_count": len(unplaced_locations),
        },
        "unplaced_locations": unplaced_locations,
    }


# --- Internal helpers ---

def _virtual_warehouse_override(overrides: dict | None) -> dict:
    if not overrides:
        return {}
    virtual_warehouse = overrides.get("virtual_warehouse")
    if isinstance(virtual_warehouse, dict):
        return virtual_warehouse
    return {}


def _coerce_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _location_center(location: dict) -> dict[str, int]:
    return {
        "x": int(location["x"] + (location["w"] / 2)),
        "y": int(location["y"] + (location["h"] / 2)),
    }


def _zone_center(zone: dict) -> dict[str, int]:
    return {
        "x": int(zone["x"] + (zone["w"] / 2)),
        "y": int(zone["y"] + (zone["h"] / 2)),
    }


def _resolve_virtual_anchor(
    entity_type: str,
    entity_code: str,
    location_scene_by_code: dict[str, dict],
    zone_scene_by_code: dict[str, dict],
) -> dict[str, int] | None:
    if entity_type == EntityType.LOCATION and entity_code in location_scene_by_code:
        return _location_center(location_scene_by_code[entity_code])
    if entity_type == EntityType.ZONE and entity_code in zone_scene_by_code:
        return _zone_center(zone_scene_by_code[entity_code])
    if entity_type in [EntityType.INVOICE, EntityType.CUSTOMER]:
        return _zone_center(FIXED_VIRTUAL_WAREHOUSE_AREAS["dispatch"])
    if entity_type == EntityType.SUPPLIER:
        return _zone_center(FIXED_VIRTUAL_WAREHOUSE_AREAS["receiving"])
    if entity_type == EntityType.VIRTUAL_BUCKET:
        return _zone_center(FIXED_VIRTUAL_WAREHOUSE_AREAS["service"])
    return None


def _display_name(user) -> str:
    if user is None:
        return "Unknown user"
    return user.display_name or user.email or "Unknown user"


def _append_location_task(location_code: str, location_scene_by_code: dict[str, dict], task: dict, worker_id: str) -> None:
    location = location_scene_by_code.get(location_code)
    if location is None:
        return
    location["active_tasks"].append(task)
    if worker_id not in location["worker_ids"]:
        location["worker_ids"].append(worker_id)

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


def _notify_new_tasks(txn: Transaction) -> None:
    """Send notifications for new available pick and drop tasks."""
    try:
        from app.notifications.fcm_service import notify_new_pick_task
        from app.notifications.websocket import broadcast_to_facility

        facility_id = str(txn.facility_id)
        picks = list(txn.picks.select_related("sku").all())
        drops = list(txn.drops.select_related("sku").all())

        for pick in picks:
            notify_new_pick_task(facility_id, pick)

        if picks or drops:
            broadcast_to_facility(facility_id, {
                "type": "new_task_available",
                "transaction_id": str(txn.pk),
                "pick_count": len(picks),
                "drop_count": len(drops),
            })
    except Exception:
        logger.debug("Failed to send new task notifications for txn %s", txn.pk)
