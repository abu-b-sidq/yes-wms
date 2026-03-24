from decimal import Decimal

import pytest

from app.core.enums import EntityType, LedgerEntryType, TransactionType
from app.inventory.models import InventoryBalance, InventoryLedger
from app.inventory.services import get_balances, get_balances_by_location, get_balances_by_sku, get_ledger
from app.operations import services as ops_services


class TestInventoryBalances:
    def test_grn_creates_balance(self, org, facility, sku):
        ops_services.create_and_execute_grn(
            org,
            facility,
            {"items": [{"sku_code": "SKU-001", "quantity": Decimal("100")}]},
        )
        balances = get_balances(org, facility=facility, sku_code="SKU-001")
        assert len(balances) == 1
        assert balances[0].quantity_on_hand == Decimal("100.0000")
        assert balances[0].quantity_available == Decimal("100.0000")

    def test_multiple_grns_accumulate(self, org, facility, sku):
        for _ in range(3):
            ops_services.create_and_execute_grn(
                org,
                facility,
                {"items": [{"sku_code": "SKU-001", "quantity": Decimal("50")}]},
            )
        balances = get_balances(org, facility=facility, sku_code="SKU-001")
        assert len(balances) == 1
        assert balances[0].quantity_on_hand == Decimal("150.0000")

    def test_move_adjusts_balances(self, org, facility, sku, zone, location, location2):
        # Seed via GRN + Putaway
        ops_services.create_and_execute_grn(
            org,
            facility,
            {"items": [{"sku_code": "SKU-001", "quantity": Decimal("100")}]},
        )
        ops_services.create_and_execute_putaway(
            org,
            facility,
            {
                "sku_code": "SKU-001",
                "dest_entity_code": "LOC-001",
                "quantity": Decimal("100"),
            },
        )
        ops_services.create_and_execute_move(
            org,
            facility,
            {
                "sku_code": "SKU-001",
                "source_entity_code": "LOC-001",
                "dest_entity_code": "LOC-002",
                "quantity": Decimal("40"),
            },
        )
        by_loc1 = get_balances_by_location(org, facility, "LOC-001")
        by_loc2 = get_balances_by_location(org, facility, "LOC-002")

        assert len(by_loc1) == 1
        assert by_loc1[0].quantity_on_hand == Decimal("60.0000")
        assert len(by_loc2) == 1
        assert by_loc2[0].quantity_on_hand == Decimal("40.0000")

    def test_get_balances_by_sku(self, org, facility, sku, zone, location, location2):
        ops_services.create_and_execute_grn(
            org,
            facility,
            {"items": [{"sku_code": "SKU-001", "quantity": Decimal("200")}]},
        )
        ops_services.create_and_execute_putaway(
            org,
            facility,
            {
                "sku_code": "SKU-001",
                "dest_entity_code": "LOC-001",
                "quantity": Decimal("120"),
            },
        )
        ops_services.create_and_execute_putaway(
            org,
            facility,
            {
                "sku_code": "SKU-001",
                "dest_entity_code": "LOC-002",
                "quantity": Decimal("80"),
            },
        )
        by_sku = get_balances_by_sku(org, facility, "SKU-001")
        # Should have balances at LOC-001, LOC-002, and PRE_PUTAWAY (0 after putaways)
        location_balances = [
            b for b in by_sku if b.entity_type == EntityType.LOCATION
        ]
        assert len(location_balances) == 2


class TestInventoryLedger:
    def test_grn_creates_ledger_entries(self, org, facility, sku):
        txn = ops_services.create_and_execute_grn(
            org,
            facility,
            {
                "items": [
                    {"sku_code": "SKU-001", "quantity": Decimal("100")},
                ],
            },
        )
        entries = get_ledger(org, transaction_id=str(txn.id))
        assert len(entries) == 1
        assert entries[0].entry_type == LedgerEntryType.DROP
        assert entries[0].quantity == Decimal("100.0000")

    def test_move_creates_two_ledger_entries(self, org, facility, sku, zone, location, location2):
        ops_services.create_and_execute_grn(
            org,
            facility,
            {"items": [{"sku_code": "SKU-001", "quantity": Decimal("100")}]},
        )
        ops_services.create_and_execute_putaway(
            org,
            facility,
            {
                "sku_code": "SKU-001",
                "dest_entity_code": "LOC-001",
                "quantity": Decimal("100"),
            },
        )
        txn = ops_services.create_and_execute_move(
            org,
            facility,
            {
                "sku_code": "SKU-001",
                "source_entity_code": "LOC-001",
                "dest_entity_code": "LOC-002",
                "quantity": Decimal("25"),
            },
        )
        entries = get_ledger(org, transaction_id=str(txn.id))
        assert len(entries) == 2
        pick_entry = [e for e in entries if e.entry_type == LedgerEntryType.PICK][0]
        drop_entry = [e for e in entries if e.entry_type == LedgerEntryType.DROP][0]
        assert pick_entry.quantity == Decimal("-25.0000")
        assert drop_entry.quantity == Decimal("25.0000")

    def test_ledger_running_balance(self, org, facility, sku):
        ops_services.create_and_execute_grn(
            org,
            facility,
            {"items": [{"sku_code": "SKU-001", "quantity": Decimal("100")}]},
        )
        ops_services.create_and_execute_grn(
            org,
            facility,
            {"items": [{"sku_code": "SKU-001", "quantity": Decimal("50")}]},
        )
        entries = get_ledger(org, facility=facility, sku_code="SKU-001")
        # Most recent first (ordered by -created_at)
        assert entries[0].balance_after == Decimal("150.0000")
        assert entries[1].balance_after == Decimal("100.0000")
