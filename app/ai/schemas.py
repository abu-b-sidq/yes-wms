"""Django Ninja schemas for AI chat endpoints."""
from __future__ import annotations

from typing import Any

from ninja import Schema


class ChatRequest(Schema):
    conversation_id: str
    message: str = ""
    confirm_action: dict[str, Any] | None = None
    model_provider: str | None = None
    model_name: str | None = None


class CreateConversationRequest(Schema):
    model_provider: str = "ollama"
    model_name: str = "llama3.1"


class UpdateConversationRequest(Schema):
    model_provider: str
    model_name: str


class ConversationOut(Schema):
    id: str
    title: str
    model_provider: str
    model_name: str
    is_active: bool
    created_at: str
    updated_at: str


class MessageOut(Schema):
    id: str
    role: str
    content: str
    components: Any | None = None
    tool_calls: Any | None = None
    created_at: str


class ConversationDetailOut(Schema):
    id: str
    title: str
    model_provider: str
    model_name: str
    is_active: bool
    created_at: str
    updated_at: str
    messages: list[MessageOut]


class ModelInfo(Schema):
    provider: str
    models: list[str]
    is_available: bool
