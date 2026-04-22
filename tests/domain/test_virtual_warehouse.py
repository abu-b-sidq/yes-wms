from decimal import Decimal

import pytest
from django.utils import timezone

from app.core.enums import EntityType, TaskStatus, TransactionType
from app.inventory.models import InventoryBalance
from app.masters.models import AppUser, FacilityLocation, FacilityZone
from app.operations import services as operation_services


pytestmark = pytest.mark.django_db


def _configure_layout(facility, zone, location, *, x: int, y: int) -> None:
    FacilityZone.objects.filter(facility=facility, zone=zone).update(
        overrides={
            "virtual_warehouse": {
                "kind": "storage",
                "x": 120,
                "y": 120,
                "w": 620,
                "h": 260,
                "label": zone.name,
            },
        },
    )
    FacilityLocation.objects.filter(facility=facility, location=location).update(
        overrides={
            "virtual_warehouse": {
                "kind": "rack",
                "x": x,
                "y": y,
                "w": 56,
                "h": 28,
            },
        },
    )


def _seed_location_balance(org, facility, sku, location_code: str, quantity: str) -> None:
    InventoryBalance.objects.create(
        org=org,
        facility=facility,
        sku=sku,
        entity_type=EntityType.LOCATION,
        entity_code=location_code,
        batch_number="",
        quantity_on_hand=Decimal(quantity),
        quantity_available=Decimal(quantity),
        quantity_reserved=Decimal("0"),
    )


def test_virtual_warehouse_completed_pick_with_incomplete_drop_contributes_to_worker_stock(
    org,
    facility,
    sku,
    zone,
    location,
    location2,
    create_app_user,
):
    _configure_layout(facility, zone, location, x=200, y=220)
    _configure_layout(facility, zone, location2, x=360, y=320)
    _seed_location_balance(org, facility, sku, location.code, "8.0000")

    user = create_app_user(display_name="Worker One")
    txn = operation_services.create_transaction(
        org,
        facility,
        {
            "transaction_type": TransactionType.MOVE,
            "reference_number": "MOVE-201",
            "picks": [
                {
                    "sku_code": sku.code,
                    "source_entity_type": EntityType.LOCATION,
                    "source_entity_code": location.code,
                    "quantity": "3.0000",
                },
            ],
            "drops": [
                {
                    "sku_code": sku.code,
                    "dest_entity_type": EntityType.LOCATION,
                    "dest_entity_code": location2.code,
                    "quantity": "3.0000",
                },
            ],
        },
        user=str(user.pk),
    )
    pick = txn.picks.get()
    drop = txn.drops.get()
    completed_at = timezone.now()
    pick.assigned_to = user
    pick.task_status = TaskStatus.COMPLETED
    pick.task_completed_at = completed_at
    pick.save(update_fields=["assigned_to", "task_status", "task_completed_at", "updated_at"])
    drop.assigned_to = user
    drop.task_status = TaskStatus.ASSIGNED
    drop.save(update_fields=["assigned_to", "task_status", "updated_at"])

    scene = operation_services.get_virtual_warehouse(org, facility)

    assert scene["summary"]["user_quantity"] == Decimal("3.0000")
    assert len(scene["task_links"]) == 1
    assert scene["task_links"][0]["source_entity_code"] == location.code
    assert scene["task_links"][0]["dest_entity_code"] == location2.code
    assert scene["workers"][0]["state"] == "carrying"
    assert scene["workers"][0]["display_name"] == "Worker One"


def test_virtual_warehouse_completed_drop_removes_carried_stock(
    org,
    facility,
    sku,
    zone,
    location,
    location2,
    create_app_user,
):
    _configure_layout(facility, zone, location, x=220, y=220)
    _configure_layout(facility, zone, location2, x=420, y=320)

    user = create_app_user(display_name="Worker One")
    txn = operation_services.create_transaction(
        org,
        facility,
        {
            "transaction_type": TransactionType.MOVE,
            "reference_number": "MOVE-202",
            "picks": [
                {
                    "sku_code": sku.code,
                    "source_entity_type": EntityType.LOCATION,
                    "source_entity_code": location.code,
                    "quantity": "2.0000",
                },
            ],
            "drops": [
                {
                    "sku_code": sku.code,
                    "dest_entity_type": EntityType.LOCATION,
                    "dest_entity_code": location2.code,
                    "quantity": "2.0000",
                },
            ],
        },
        user=str(user.pk),
    )
    pick = txn.picks.get()
    drop = txn.drops.get()
    pick.assigned_to = user
    pick.task_status = TaskStatus.COMPLETED
    pick.task_completed_at = timezone.now()
    pick.save(update_fields=["assigned_to", "task_status", "task_completed_at", "updated_at"])
    drop.assigned_to = user
    drop.task_status = TaskStatus.COMPLETED
    drop.task_completed_at = timezone.now()
    drop.save(update_fields=["assigned_to", "task_status", "task_completed_at", "updated_at"])

    scene = operation_services.get_virtual_warehouse(org, facility)

    assert scene["summary"]["user_quantity"] == Decimal("0")
    assert scene["task_links"] == []
    assert scene["workers"] == []


def test_virtual_warehouse_active_pick_without_completed_pick_pins_worker_to_source(
    org,
    facility,
    sku,
    zone,
    location,
    location2,
    create_app_user,
):
    _configure_layout(facility, zone, location, x=260, y=260)
    _configure_layout(facility, zone, location2, x=420, y=320)

    user = create_app_user(display_name="Picker One")
    txn = operation_services.create_transaction(
        org,
        facility,
        {
            "transaction_type": TransactionType.MOVE,
            "reference_number": "MOVE-203",
            "picks": [
                {
                    "sku_code": sku.code,
                    "source_entity_type": EntityType.LOCATION,
                    "source_entity_code": location.code,
                    "quantity": "1.0000",
                },
            ],
            "drops": [
                {
                    "sku_code": sku.code,
                    "dest_entity_type": EntityType.LOCATION,
                    "dest_entity_code": location2.code,
                    "quantity": "1.0000",
                },
            ],
        },
        user=str(user.pk),
    )
    pick = txn.picks.get()
    pick.assigned_to = user
    pick.task_status = TaskStatus.IN_PROGRESS
    pick.task_started_at = timezone.now()
    pick.save(update_fields=["assigned_to", "task_status", "task_started_at", "updated_at"])

    scene = operation_services.get_virtual_warehouse(org, facility)

    assert scene["summary"]["user_quantity"] == Decimal("0")
    assert len(scene["workers"]) == 1
    assert scene["workers"][0]["state"] == "picking"
    assert scene["workers"][0]["source_entity_code"] == location.code


def test_virtual_warehouse_locations_without_layout_are_unplaced(
    org,
    facility,
    sku,
    zone,
    location,
    location2,
):
    _configure_layout(facility, zone, location, x=180, y=200)
    _seed_location_balance(org, facility, sku, location.code, "5.0000")

    scene = operation_services.get_virtual_warehouse(org, facility)

    assert [item["code"] for item in scene["unplaced_locations"]] == [location2.code]
    assert [item["code"] for item in scene["locations"]] == [location.code]
