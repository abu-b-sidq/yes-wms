from __future__ import annotations

import asyncio

from app.ai import chat_service


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
