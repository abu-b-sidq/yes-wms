from decimal import Decimal

import pytest

from app.core.enums import EntityType, TransactionStatus, TransactionType
from app.core.exceptions import InsufficientInventoryError, ValidationError
from app.inventory.models import InventoryBalance
from app.inventory.services import credit_balance
from app.operations import services
from app.operations.models import Transaction


class TestTransactionCreation:
    def test_create_move_transaction(self, org, facility, sku, zone, location, location2):
        txn = services.create_transaction(
            org,
            facility,
            {
                "transaction_type": TransactionType.MOVE,
                "picks": [
                    {
                        "sku_code": "SKU-001",
                        "source_entity_type": EntityType.LOCATION,
                        "source_entity_code": "LOC-001",
                        "quantity": Decimal("10"),
                    }
                ],
                "drops": [
                    {
                        "sku_code": "SKU-001",
                        "dest_entity_type": EntityType.LOCATION,
                        "dest_entity_code": "LOC-002",
                        "quantity": Decimal("10"),
                    }
                ],
            },
        )
        assert txn.transaction_type == TransactionType.MOVE
        assert txn.status == TransactionStatus.PENDING
        assert txn.picks.count() == 1
        assert txn.drops.count() == 1

    def test_create_grn_transaction(self, org, facility, sku):
        txn = services.create_transaction(
            org,
            facility,
            {
                "transaction_type": TransactionType.GRN,
                "drops": [
                    {
                        "sku_code": "SKU-001",
                        "dest_entity_type": EntityType.ZONE,
                        "dest_entity_code": "PRE_PUTAWAY",
                        "quantity": Decimal("100"),
                    }
                ],
            },
        )
        assert txn.transaction_type == TransactionType.GRN
        assert txn.drops.count() == 1
        assert txn.picks.count() == 0

    def test_create_move_without_picks_fails(self, org, facility, sku):
        with pytest.raises(ValidationError, match="at least 1 pick"):
            services.create_transaction(
                org,
                facility,
                {
                    "transaction_type": TransactionType.MOVE,
                    "picks": [],
                    "drops": [
                        {
                            "sku_code": "SKU-001",
                            "dest_entity_type": EntityType.LOCATION,
                            "dest_entity_code": "LOC-002",
                            "quantity": Decimal("10"),
                        }
                    ],
                },
            )

    def test_create_move_with_mismatched_pick_drop_counts_fails(self, org, facility, sku):
        with pytest.raises(ValidationError, match="matching pick and drop counts"):
            services.create_transaction(
                org,
                facility,
                {
                    "transaction_type": TransactionType.MOVE,
                    "picks": [
                        {
                            "sku_code": "SKU-001",
                            "source_entity_type": EntityType.LOCATION,
                            "source_entity_code": "LOC-001",
                            "quantity": Decimal("10"),
                        }
                    ],
                    "drops": [
                        {
                            "sku_code": "SKU-001",
                            "dest_entity_type": EntityType.LOCATION,
                            "dest_entity_code": "LOC-002",
                            "quantity": Decimal("5"),
                        },
                        {
                            "sku_code": "SKU-001",
                            "dest_entity_type": EntityType.LOCATION,
                            "dest_entity_code": "LOC-003",
                            "quantity": Decimal("5"),
                        },
                    ],
                },
            )

    def test_create_with_invalid_quantity(self, org, facility, sku):
        with pytest.raises(ValidationError, match="positive"):
            services.create_transaction(
                org,
                facility,
                {
                    "transaction_type": TransactionType.GRN,
                    "drops": [
                        {
                            "sku_code": "SKU-001",
                            "dest_entity_type": EntityType.ZONE,
                            "dest_entity_code": "PRE_PUTAWAY",
                            "quantity": Decimal("0"),
                        }
                    ],
                },
            )


class TestTransactionExecution:
    def _seed_inventory(self, org, facility, sku, entity_type, entity_code, qty):
        """Seed inventory by creating a GRN-like credit."""
        # Directly create a balance for testing
        balance, _ = InventoryBalance.objects.get_or_create(
            org=org,
            facility=facility,
            sku=sku,
            entity_type=entity_type,
            entity_code=entity_code,
            batch_number="",
            defaults={
                "quantity_on_hand": qty,
                "quantity_reserved": Decimal("0"),
                "quantity_available": qty,
            },
        )
        return balance

    def test_execute_move_transaction(self, org, facility, sku, zone, location, location2):
        self._seed_inventory(
            org, facility, sku, EntityType.LOCATION, "LOC-001", Decimal("50")
        )
        txn = services.create_transaction(
            org,
            facility,
            {
                "transaction_type": TransactionType.MOVE,
                "picks": [
                    {
                        "sku_code": "SKU-001",
                        "source_entity_type": EntityType.LOCATION,
                        "source_entity_code": "LOC-001",
                        "quantity": Decimal("10"),
                    }
                ],
                "drops": [
                    {
                        "sku_code": "SKU-001",
                        "dest_entity_type": EntityType.LOCATION,
                        "dest_entity_code": "LOC-002",
                        "quantity": Decimal("10"),
                    }
                ],
            },
        )
        executed = services.execute_transaction(txn)
        assert executed.status == TransactionStatus.COMPLETED
        assert executed.started_at is not None
        assert executed.completed_at is not None

        # Check balances
        source = InventoryBalance.objects.get(
            org=org, facility=facility, sku=sku,
            entity_type=EntityType.LOCATION, entity_code="LOC-001",
        )
        dest = InventoryBalance.objects.get(
            org=org, facility=facility, sku=sku,
            entity_type=EntityType.LOCATION, entity_code="LOC-002",
        )
        assert source.quantity_on_hand == Decimal("40.0000")
        assert dest.quantity_on_hand == Decimal("10.0000")

    def test_execute_with_insufficient_inventory(self, org, facility, sku, zone, location, location2):
        self._seed_inventory(
            org, facility, sku, EntityType.LOCATION, "LOC-001", Decimal("5")
        )
        txn = services.create_transaction(
            org,
            facility,
            {
                "transaction_type": TransactionType.MOVE,
                "picks": [
                    {
                        "sku_code": "SKU-001",
                        "source_entity_type": EntityType.LOCATION,
                        "source_entity_code": "LOC-001",
                        "quantity": Decimal("10"),
                    }
                ],
                "drops": [
                    {
                        "sku_code": "SKU-001",
                        "dest_entity_type": EntityType.LOCATION,
                        "dest_entity_code": "LOC-002",
                        "quantity": Decimal("10"),
                    }
                ],
            },
        )
        with pytest.raises(InsufficientInventoryError):
            services.execute_transaction(txn)

    def test_execute_grn_creates_inventory(self, org, facility, sku):
        txn = services.create_transaction(
            org,
            facility,
            {
                "transaction_type": TransactionType.GRN,
                "drops": [
                    {
                        "sku_code": "SKU-001",
                        "dest_entity_type": EntityType.ZONE,
                        "dest_entity_code": "PRE_PUTAWAY",
                        "quantity": Decimal("100"),
                    }
                ],
            },
        )
        executed = services.execute_transaction(txn)
        assert executed.status == TransactionStatus.COMPLETED

        balance = InventoryBalance.objects.get(
            org=org, facility=facility, sku=sku,
            entity_type=EntityType.ZONE, entity_code="PRE_PUTAWAY",
        )
        assert balance.quantity_on_hand == Decimal("100.0000")


class TestConvenienceEndpoints:
    def test_create_and_execute_grn(self, org, facility, sku):
        txn = services.create_and_execute_grn(
            org,
            facility,
            {
                "items": [
                    {"sku_code": "SKU-001", "quantity": Decimal("50")},
                ],
            },
        )
        assert txn.status == TransactionStatus.COMPLETED
        assert txn.transaction_type == TransactionType.GRN

    def test_create_and_execute_move(self, org, facility, sku, zone, location, location2):
        # First seed inventory via GRN
        services.create_and_execute_grn(
            org,
            facility,
            {"items": [{"sku_code": "SKU-001", "quantity": Decimal("100")}]},
        )
        # Putaway to a location
        services.create_and_execute_putaway(
            org,
            facility,
            {
                "sku_code": "SKU-001",
                "dest_entity_code": "LOC-001",
                "quantity": Decimal("100"),
            },
        )
        # Move between locations
        txn = services.create_and_execute_move(
            org,
            facility,
            {
                "sku_code": "SKU-001",
                "source_entity_code": "LOC-001",
                "dest_entity_code": "LOC-002",
                "quantity": Decimal("30"),
            },
        )
        assert txn.status == TransactionStatus.COMPLETED

        source = InventoryBalance.objects.get(
            org=org, facility=facility, sku=sku,
            entity_type=EntityType.LOCATION, entity_code="LOC-001",
        )
        dest = InventoryBalance.objects.get(
            org=org, facility=facility, sku=sku,
            entity_type=EntityType.LOCATION, entity_code="LOC-002",
        )
        assert source.quantity_on_hand == Decimal("70.0000")
        assert dest.quantity_on_hand == Decimal("30.0000")


class TestCancelTransaction:
    def test_cancel_pending_transaction(self, org, facility, sku):
        txn = services.create_transaction(
            org,
            facility,
            {
                "transaction_type": TransactionType.GRN,
                "drops": [
                    {
                        "sku_code": "SKU-001",
                        "dest_entity_type": EntityType.ZONE,
                        "dest_entity_code": "PRE_PUTAWAY",
                        "quantity": Decimal("10"),
                    }
                ],
            },
        )
        cancelled = services.cancel_transaction(txn)
        assert cancelled.status == TransactionStatus.CANCELLED
        assert cancelled.cancelled_at is not None
