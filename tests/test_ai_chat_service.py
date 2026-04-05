from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.ai import chat_service
from app.mcp import tools as mcp_tools


def test_build_prefetched_context_prompt_with_hits():
    prompt = chat_service._build_prefetched_context_prompt([
        {
            "type": "knowledge",
            "id": "knowledge/grn-1",
            "score": 0.97,
            "text": "GRN items should land in PRE_PUTAWAY before putaway is executed.",
        }
    ])

    assert "Semantic context has already been prefetched" in prompt
    assert "type=knowledge" in prompt
    assert "score=0.97" in prompt
    assert "PRE_PUTAWAY" in prompt


def test_build_prefetched_context_prompt_without_hits():
    prompt = chat_service._build_prefetched_context_prompt([])

    assert "Semantic context has already been prefetched" in prompt
    assert "no relevant matches were found" in prompt


def test_prefetch_semantic_context_calls_semantic_search(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_search(**kwargs):
        captured.update(kwargs)
        return [{"type": "knowledge", "id": "k1", "score": 0.91, "text": "Putaway SOP"}]

    monkeypatch.setattr("app.mcp.tools.wms_semantic_search", fake_search)

    results = asyncio.run(
        chat_service._prefetch_semantic_context(
            "how do I do putaway",
            uid="firebase-user-1",
            org_id="test-org",
        )
    )

    assert results == [{"type": "knowledge", "id": "k1", "score": 0.91, "text": "Putaway SOP"}]
    assert captured["query"] == "how do I do putaway"
    assert captured["uid"] == "firebase-user-1"
    assert captured["org_id"] == "test-org"
    assert captured["limit"] == chat_service.PREFETCH_RAG_LIMIT
    assert captured["content_types"] == list(chat_service.PREFETCH_RAG_CONTENT_TYPES)


def test_prefetch_semantic_context_skips_blank_messages():
    results = asyncio.run(
        chat_service._prefetch_semantic_context(
            "   ",
            uid="firebase-user-1",
            org_id="test-org",
        )
    )

    assert results is None


def test_build_assistant_tool_message_keeps_tool_arguments_as_objects():
    message = chat_service._build_assistant_tool_message(
        "",
        [
            {
                "id": "call_1",
                "name": "wms_list_transactions",
                "arguments": {"status": "PENDING"},
            }
        ],
    )

    assert message["role"] == "assistant"
    assert message["tool_calls"][0]["function"]["arguments"] == {"status": "PENDING"}
    assert not isinstance(message["tool_calls"][0]["function"]["arguments"], str)


def test_inventory_balance_tool_unpacks_paginated_service_result(monkeypatch):
    fake_access = SimpleNamespace(allowed_facility_codes=[])
    fake_org = SimpleNamespace(id="testorg")
    fake_facility = SimpleNamespace(code="FAC-001")
    fake_balance = SimpleNamespace(
        id="bal-1",
        facility_id="fac-1",
        facility=fake_facility,
        sku=SimpleNamespace(code="SKU-001"),
        entity_type="LOCATION",
        entity_code="LOC-001",
        batch_number="",
        quantity_on_hand=Decimal("10"),
        quantity_reserved=Decimal("2"),
        quantity_available=Decimal("8"),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    captured: dict[str, object] = {}

    def fake_get_balances(org, facility=None, sku_code=None, entity_type=None, entity_code=None):
        captured.update({
            "org": org,
            "facility": facility,
            "sku_code": sku_code,
            "entity_type": entity_type,
            "entity_code": entity_code,
        })
        return [fake_balance], 1

    monkeypatch.setattr("app.mcp.tools._check", lambda uid, org_id, permission=None: fake_access)
    monkeypatch.setattr("app.mcp.tools._resolve_org", lambda org_id: fake_org)
    monkeypatch.setattr("app.mcp.tools._resolve_facility", lambda org, facility_id: fake_facility)
    monkeypatch.setattr("app.auth.authorization.enforce_facility_scope", lambda access, facility_id: None)
    monkeypatch.setattr("app.inventory.services.get_balances", fake_get_balances)

    result = asyncio.run(
        mcp_tools.wms_get_inventory_balances(
            org_id="testorg",
            facility_id="FAC-001",
            sku_code="SKU-001",
            entity_type="LOCATION",
            entity_code="LOC-001",
            uid="firebase-user-1",
        )
    )

    assert captured == {
        "org": fake_org,
        "facility": fake_facility,
        "sku_code": "SKU-001",
        "entity_type": "LOCATION",
        "entity_code": "LOC-001",
    }
    assert result == [
        {
            "id": "bal-1",
            "facility_code": "FAC-001",
            "sku_code": "SKU-001",
            "entity_type": "LOCATION",
            "entity_code": "LOC-001",
            "batch_number": "",
            "quantity_on_hand": "10",
            "quantity_reserved": "2",
            "quantity_available": "8",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
    ]
