from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.ai import chat_service
from app.ai.llm_providers import StreamChunk, ToolCall
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


def test_list_transactions_tool_unpacks_paginated_service_result(monkeypatch):
    fake_access = SimpleNamespace(allowed_facility_codes=[])
    fake_org = SimpleNamespace(id="testorg")
    fake_facility = SimpleNamespace(code="FAC-001")
    fake_transaction = SimpleNamespace(
        id="txn-1",
        transaction_type="MOVE",
        status="PENDING",
        reference_number="REF-001",
        notes="Move stock",
        document_url="",
        created_by="firebase-user-1",
        picks=SimpleNamespace(all=lambda: []),
        drops=SimpleNamespace(all=lambda: []),
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        started_at=None,
        completed_at=None,
        cancelled_at=None,
    )
    captured: dict[str, object] = {}

    def fake_list_transactions(
        org,
        facility=None,
        transaction_type=None,
        status=None,
        date_from=None,
        date_to=None,
    ):
        captured.update({
            "org": org,
            "facility": facility,
            "transaction_type": transaction_type,
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
        })
        return [fake_transaction], 1

    monkeypatch.setattr("app.mcp.tools._check", lambda uid, org_id, permission=None: fake_access)
    monkeypatch.setattr("app.mcp.tools._resolve_org", lambda org_id: fake_org)
    monkeypatch.setattr("app.mcp.tools._resolve_facility", lambda org, facility_id: fake_facility)
    monkeypatch.setattr("app.auth.authorization.enforce_facility_scope", lambda access, facility_id: None)
    monkeypatch.setattr("app.operations.services.list_transactions", fake_list_transactions)

    result = asyncio.run(
        mcp_tools.wms_list_transactions(
            org_id="testorg",
            facility_id="FAC-001",
            transaction_type="MOVE",
            status="PENDING",
            date_from="2026-01-01",
            date_to="2026-01-31",
            uid="firebase-user-1",
        )
    )

    assert captured == {
        "org": fake_org,
        "facility": fake_facility,
        "transaction_type": "MOVE",
        "status": "PENDING",
        "date_from": "2026-01-01",
        "date_to": "2026-01-31",
    }
    assert result == [
        {
            "id": "txn-1",
            "transaction_type": "MOVE",
            "status": "PENDING",
            "reference_number": "REF-001",
            "notes": "Move stock",
            "document_url": None,
            "created_by": "firebase-user-1",
            "picks": [],
            "drops": [],
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-02T00:00:00+00:00",
            "started_at": None,
            "completed_at": None,
            "cancelled_at": None,
        }
    ]


def _enable_caplog_for_ai_logger(monkeypatch) -> None:
    app_logger = logging.getLogger("app")
    ai_logger = logging.getLogger("app.ai")
    chat_logger = logging.getLogger("app.ai.chat_service")

    monkeypatch.setattr(app_logger, "handlers", [])
    monkeypatch.setattr(app_logger, "propagate", True)
    monkeypatch.setattr(ai_logger, "handlers", [])
    monkeypatch.setattr(ai_logger, "propagate", True)
    monkeypatch.setattr(chat_logger, "handlers", [])
    monkeypatch.setattr(chat_logger, "propagate", True)


async def _collect_events(**kwargs):
    events = []
    async for event in chat_service.handle_chat_message(**kwargs):
        events.append(event)
    return events


class _FakeMessages:
    def __init__(self):
        self._items = []

    def count(self):
        return len(self._items)

    def order_by(self, *_args):
        return list(self._items)


class _FakeConversation:
    def __init__(self, conversation_id: str):
        self.id = conversation_id
        self.model_provider = "ollama"
        self.model_name = "llama3.1"
        self.facility_id = "FAC-001"
        self.title = "New conversation"
        self.updated_at = None
        self.messages = _FakeMessages()

    def save(self, update_fields=None):
        self.updated_at = update_fields


class _FakeConversationManager:
    def __init__(self, conversation):
        self.conversation = conversation

    def select_related(self, *_args):
        return self

    def get(self, *, id):
        assert str(id) == str(self.conversation.id)
        return self.conversation


class _FakeMessageManager:
    def __init__(self):
        self.created = []

    def create(
        self,
        *,
        conversation,
        role,
        content,
        components=None,
        tool_calls=None,
        tool_results=None,
    ):
        message = SimpleNamespace(
            id=f"msg-{len(self.created) + 1}",
            conversation=conversation,
            role=role,
            content=content,
            components=components,
            tool_calls=tool_calls,
            tool_results=tool_results,
        )
        self.created.append(message)
        conversation.messages._items.append(message)
        return message


def _install_fake_ai_models(monkeypatch, conversation):
    message_manager = _FakeMessageManager()
    monkeypatch.setattr(
        "app.ai.models.Conversation",
        SimpleNamespace(objects=_FakeConversationManager(conversation)),
    )
    monkeypatch.setattr(
        "app.ai.models.Message",
        SimpleNamespace(
            objects=message_manager,
            Role=SimpleNamespace(USER="user", ASSISTANT="assistant", TOOL="tool", SYSTEM="system"),
        ),
    )
    return message_manager


def test_handle_chat_message_logs_execution_trace_for_conversation(caplog, monkeypatch):
    _enable_caplog_for_ai_logger(monkeypatch)
    caplog.set_level(logging.INFO, logger="app.ai.chat_service")

    conversation = _FakeConversation(str(uuid.uuid4()))
    _install_fake_ai_models(monkeypatch, conversation)

    class FakeProvider:
        async def chat_completion(self, messages, tools, model):
            yield StreamChunk(delta_text="Here is the summary.")

    async def fake_prefetch(*args, **kwargs):
        return [{"type": "knowledge", "id": "kb-1", "score": 0.98, "text": "Putaway SOP"}]

    async def fake_upsert_embedding(*args, **kwargs):
        return None

    monkeypatch.setattr("app.ai.chat_service.get_provider", lambda provider_name: FakeProvider())
    monkeypatch.setattr("app.ai.chat_service._prefetch_semantic_context", fake_prefetch)
    monkeypatch.setattr("app.ai.embeddings.upsert_embedding", fake_upsert_embedding)

    events = asyncio.run(
        _collect_events(
            conversation_id=str(conversation.id),
            user_message="Summarize the latest activity",
            uid="worker-ai-log-1",
            org_id="testorg",
            facility_id="FAC-001",
            facility_name="Test Facility",
        )
    )

    assert events[-1].event == "done"

    records = [
        record
        for record in caplog.records
        if record.name == "app.ai.chat_service" and getattr(record, "event_name", None) == "ai.thread.execution"
    ]
    assert records

    event_data = records[-1].event_data
    assert event_data["thread_id"] == str(conversation.id)
    assert event_data["conversation_id"] == str(conversation.id)
    assert event_data["status"] == "completed"

    steps = [item["step"] for item in event_data["execution_log"]]
    assert "conversation_loaded" in steps
    assert "user_message_saved" in steps
    assert "semantic_context_prefetched" in steps
    assert "assistant_message_saved" in steps


def test_handle_chat_message_persists_json_safe_tool_results(monkeypatch):
    conversation = _FakeConversation(str(uuid.uuid4()))
    message_manager = _install_fake_ai_models(monkeypatch, conversation)

    class FakeProvider:
        def __init__(self):
            self.round = 0

        async def chat_completion(self, messages, tools, model):
            if self.round == 0:
                self.round += 1
                yield StreamChunk(
                    tool_calls=[
                        ToolCall(
                            id="tool-call-1",
                            name="wms_execute_analytical_query",
                            arguments={"sql": "SELECT quantity FROM app_transaction"},
                        )
                    ]
                )
                return

            yield StreamChunk(delta_text='{"text":"Done","components":[]}')

    async def fake_prefetch(*args, **kwargs):
        return []

    async def fake_execute_tool(tool_name, arguments, uid, org_id, facility_id=None):
        return {
            "columns": ["quantity", "captured_at"],
            "rows": [
                {
                    "quantity": Decimal("12.5000"),
                    "captured_at": datetime(2026, 4, 5, 18, 32, 41, tzinfo=timezone.utc),
                }
            ],
            "row_count": 1,
            "truncated": False,
            "scope_applied": {"org_id": org_id},
        }

    async def fake_upsert_embedding(*args, **kwargs):
        return None

    monkeypatch.setattr("app.ai.chat_service.get_provider", lambda provider_name: FakeProvider())
    monkeypatch.setattr("app.ai.chat_service._prefetch_semantic_context", fake_prefetch)
    monkeypatch.setattr("app.ai.chat_service.execute_tool", fake_execute_tool)
    monkeypatch.setattr("app.ai.embeddings.upsert_embedding", fake_upsert_embedding)

    events = asyncio.run(
        _collect_events(
            conversation_id=str(conversation.id),
            user_message="Run analytics",
            uid="firebase-user-1",
            org_id="testorg",
            facility_id="FAC-001",
            facility_name="Test Facility",
        )
    )

    assert events[-1].event == "done"
    assistant_message = message_manager.created[-1]
    assert assistant_message.role == "assistant"
    assert assistant_message.tool_calls == [
        {
            "tool": "wms_execute_analytical_query",
            "args": {"sql": "SELECT quantity FROM app_transaction"},
            "result": {
                "columns": ["quantity", "captured_at"],
                "rows": [
                    {
                        "quantity": "12.5000",
                        "captured_at": "2026-04-05T18:32:41+00:00",
                    }
                ],
                "row_count": 1,
                "truncated": False,
                "scope_applied": {"org_id": "testorg"},
            },
        }
    ]


def test_handle_chat_message_logs_failed_execution_trace(caplog, monkeypatch):
    _enable_caplog_for_ai_logger(monkeypatch)
    caplog.set_level(logging.INFO, logger="app.ai.chat_service")

    conversation = _FakeConversation(str(uuid.uuid4()))
    _install_fake_ai_models(monkeypatch, conversation)

    class FailingProvider:
        async def chat_completion(self, messages, tools, model):
            raise RuntimeError("provider unavailable")
            yield  # pragma: no cover

    async def fake_prefetch(*args, **kwargs):
        return []

    monkeypatch.setattr("app.ai.chat_service.get_provider", lambda provider_name: FailingProvider())
    monkeypatch.setattr("app.ai.chat_service._prefetch_semantic_context", fake_prefetch)

    with pytest.raises(RuntimeError, match="provider unavailable"):
        asyncio.run(
            _collect_events(
                conversation_id=str(conversation.id),
                user_message="What happened today?",
                uid="worker-ai-log-2",
                org_id="testorg",
                facility_id="FAC-001",
                facility_name="Test Facility",
            )
        )

    records = [
        record
        for record in caplog.records
        if record.name == "app.ai.chat_service" and getattr(record, "event_name", None) == "ai.thread.execution"
    ]
    assert records

    event_data = records[-1].event_data
    assert event_data["thread_id"] == str(conversation.id)
    assert event_data["status"] == "failed"
    assert event_data["error"]["type"] == "RuntimeError"

    steps = [item["step"] for item in event_data["execution_log"]]
    assert steps[-1] == "thread_failed"
