from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.ai import routes, schemas


class _DummyEvent:
    def encode(self) -> str:
        return "event: done\ndata: {}\n\n"


class _DummyStreamingResponse:
    def __init__(self, stream, content_type: str):
        self.content_type = content_type
        self.headers: dict[str, str] = {}
        self.chunks = asyncio.run(self._collect(stream))

    async def _collect(self, stream):
        return [chunk async for chunk in stream]

    def __setitem__(self, key: str, value: str) -> None:
        self.headers[key] = value


def test_chat_passes_facility_code_to_tool_context(monkeypatch):
    captured: dict = {}
    org = SimpleNamespace(id="testorg")
    facility = SimpleNamespace(
        id="4419847f-afd5-4ca6-a7d1-bb3bf6e56b7f",
        code="testfacility1",
        name="Test Facility 1",
    )
    request = SimpleNamespace(
        auth_context=SimpleNamespace(uid="firebase-user-1"),
    )

    async def fake_handle_chat_message(**kwargs):
        captured.update(kwargs)
        yield _DummyEvent()

    monkeypatch.setattr("app.ai.routes.authorize_request", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.ai.routes.resolve_request_tenant", lambda *args, **kwargs: (org, facility))
    monkeypatch.setattr("app.ai.chat_service.handle_chat_message", fake_handle_chat_message)
    monkeypatch.setattr("app.ai.routes.StreamingHttpResponse", _DummyStreamingResponse)

    payload = schemas.ChatRequest(conversation_id="conv-1", message="show transactions")
    response = routes.chat(request, payload)

    assert response.content_type == "text/event-stream"
    assert captured["org_id"] == "testorg"
    assert captured["facility_id"] == "testfacility1"
    assert captured["facility_name"] == "Test Facility 1"
