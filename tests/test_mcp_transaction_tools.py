from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.mcp import tools as mcp_tools


def _fake_transaction(
    transaction_type: str,
    *,
    status: str = "PENDING",
    reference_number: str = "",
    notes: str = "",
    created_by: str = "firebase-user-1",
):
    return SimpleNamespace(
        id="txn-1",
        transaction_type=transaction_type,
        status=status,
        reference_number=reference_number,
        notes=notes,
        document_url="",
        created_by=created_by,
        facility=SimpleNamespace(code="FAC-001"),
        picks=SimpleNamespace(all=lambda: []),
        drops=SimpleNamespace(all=lambda: []),
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        started_at=None,
        completed_at=None,
        cancelled_at=None,
    )


@pytest.mark.parametrize(
    ("tool_name", "tool_kwargs", "blocked_service", "expected_data"),
    [
        (
            "wms_move_inventory",
            {
                "sku_code": "SKU-001",
                "source_entity_code": "LOC-001",
                "dest_entity_code": "LOC-002",
                "quantity": "10",
                "source_entity_type": "LOCATION",
                "dest_entity_type": "LOCATION",
                "batch_number": "B-1",
                "reference_number": "MOVE-001",
            },
            "create_and_execute_move",
            {
                "transaction_type": "MOVE",
                "reference_number": "MOVE-001",
                "notes": "",
                "picks": [
                    {
                        "sku_code": "SKU-001",
                        "source_entity_type": "LOCATION",
                        "source_entity_code": "LOC-001",
                        "quantity": Decimal("10"),
                        "batch_number": "B-1",
                    }
                ],
                "drops": [
                    {
                        "sku_code": "SKU-001",
                        "dest_entity_type": "LOCATION",
                        "dest_entity_code": "LOC-002",
                        "quantity": Decimal("10"),
                        "batch_number": "B-1",
                    }
                ],
            },
        ),
        (
            "wms_create_grn",
            {
                "items": [
                    {
                        "sku_code": "SKU-001",
                        "quantity": "5",
                        "dest_entity_code": "PRE_PUTAWAY",
                        "dest_entity_type": "ZONE",
                        "batch_number": "LOT-1",
                    }
                ],
                "reference_number": "GRN-001",
                "notes": "Incoming goods",
            },
            "create_and_execute_grn",
            {
                "transaction_type": "GRN",
                "reference_number": "GRN-001",
                "notes": "Incoming goods",
                "picks": [],
                "drops": [
                    {
                        "sku_code": "SKU-001",
                        "dest_entity_type": "ZONE",
                        "dest_entity_code": "PRE_PUTAWAY",
                        "quantity": Decimal("5"),
                        "batch_number": "LOT-1",
                    }
                ],
            },
        ),
        (
            "wms_putaway",
            {
                "sku_code": "SKU-001",
                "dest_entity_code": "LOC-001",
                "quantity": "8.5",
                "source_entity_code": "PRE_PUTAWAY",
                "source_entity_type": "ZONE",
                "dest_entity_type": "LOCATION",
                "batch_number": "LOT-2",
                "reference_number": "PUT-001",
            },
            "create_and_execute_putaway",
            {
                "transaction_type": "PUTAWAY",
                "reference_number": "PUT-001",
                "notes": "",
                "picks": [
                    {
                        "sku_code": "SKU-001",
                        "source_entity_type": "ZONE",
                        "source_entity_code": "PRE_PUTAWAY",
                        "quantity": Decimal("8.5"),
                        "batch_number": "LOT-2",
                    }
                ],
                "drops": [
                    {
                        "sku_code": "SKU-001",
                        "dest_entity_type": "LOCATION",
                        "dest_entity_code": "LOC-001",
                        "quantity": Decimal("8.5"),
                        "batch_number": "LOT-2",
                    }
                ],
            },
        ),
        (
            "wms_order_pick",
            {
                "sku_code": "SKU-001",
                "source_entity_code": "LOC-001",
                "dest_entity_code": "INV-001",
                "quantity": "3",
                "source_entity_type": "LOCATION",
                "dest_entity_type": "INVOICE",
                "batch_number": "LOT-3",
                "reference_number": "SO-001",
            },
            "create_and_execute_order_pick",
            {
                "transaction_type": "ORDER_PICK",
                "reference_number": "SO-001",
                "notes": "",
                "picks": [
                    {
                        "sku_code": "SKU-001",
                        "source_entity_type": "LOCATION",
                        "source_entity_code": "LOC-001",
                        "quantity": Decimal("3"),
                        "batch_number": "LOT-3",
                    }
                ],
                "drops": [
                    {
                        "sku_code": "SKU-001",
                        "dest_entity_type": "INVOICE",
                        "dest_entity_code": "INV-001",
                        "quantity": Decimal("3"),
                        "batch_number": "LOT-3",
                    }
                ],
            },
        ),
    ],
)
def test_mcp_transaction_shortcuts_create_pending_transactions(
    monkeypatch,
    tool_name: str,
    tool_kwargs: dict,
    blocked_service: str,
    expected_data: dict,
):
    fake_access = SimpleNamespace(allowed_facility_codes=[])
    fake_org = SimpleNamespace(id="testorg")
    fake_facility = SimpleNamespace(code="FAC-001")
    captured: dict[str, object] = {}

    def fake_create_transaction(org, facility, data, user=""):
        captured["org"] = org
        captured["facility"] = facility
        captured["data"] = data
        captured["user"] = user
        return _fake_transaction(
            data["transaction_type"],
            reference_number=data.get("reference_number", ""),
            notes=data.get("notes", ""),
            created_by=user,
        )

    def should_not_execute(*_args, **_kwargs):
        raise AssertionError("MCP shortcut should not auto-execute transactions.")

    monkeypatch.setattr("app.mcp.tools._check", lambda uid, org_id, permission=None: fake_access)
    monkeypatch.setattr("app.mcp.tools._resolve_org", lambda org_id: fake_org)
    monkeypatch.setattr("app.mcp.tools._resolve_facility", lambda org, facility_id: fake_facility)
    monkeypatch.setattr(f"app.operations.services.{blocked_service}", should_not_execute)
    monkeypatch.setattr("app.operations.services.create_transaction", fake_create_transaction)

    result = asyncio.run(
        getattr(mcp_tools, tool_name)(
            org_id="testorg",
            facility_id="FAC-001",
            uid="firebase-user-1",
            **tool_kwargs,
        )
    )

    assert captured == {
        "org": fake_org,
        "facility": fake_facility,
        "data": expected_data,
        "user": "firebase-user-1",
    }
    assert result["transaction_type"] == expected_data["transaction_type"]
    assert result["status"] == "PENDING"
    assert result["completed_at"] is None


def test_mcp_execute_transaction_keeps_transaction_pending(monkeypatch):
    fake_access = SimpleNamespace(allowed_facility_codes=[])
    fake_org = SimpleNamespace(id="testorg")
    fake_txn = _fake_transaction("MOVE", reference_number="MOVE-001")

    def should_not_execute(*_args, **_kwargs):
        raise AssertionError("MCP execute should not complete the transaction.")

    monkeypatch.setattr("app.mcp.tools._check", lambda uid, org_id, permission=None: fake_access)
    monkeypatch.setattr("app.mcp.tools._resolve_org", lambda org_id: fake_org)
    monkeypatch.setattr("app.operations.services.get_transaction", lambda org, transaction_id: fake_txn)
    monkeypatch.setattr("app.operations.services.execute_transaction", should_not_execute)

    result = asyncio.run(
        mcp_tools.wms_execute_transaction(
            org_id="testorg",
            transaction_id="txn-1",
            uid="firebase-user-1",
        )
    )

    assert result["id"] == "txn-1"
    assert result["status"] == "PENDING"
    assert result["started_at"] is None
    assert result["completed_at"] is None
