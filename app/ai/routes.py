"""AI chat API routes — SSE streaming chat, conversation CRUD, model listing."""
from __future__ import annotations

import asyncio
import logging

from django.http import StreamingHttpResponse
from ninja import Router

from app.ai import schemas
from app.auth.authorization import authorize_request
from app.core.response import success_response
from app.core.tenant import resolve_request_tenant

logger = logging.getLogger(__name__)

router = Router(tags=["ai"])


# ---------------------------------------------------------------------------
# POST /ai/chat — streaming SSE
# ---------------------------------------------------------------------------

@router.post("/chat", url_name="ai_chat")
def chat(request, payload: schemas.ChatRequest):
    """Send a message and receive a streaming SSE response."""
    authorize_request(request, require_firebase=True)
    org, facility = resolve_request_tenant(request)
    uid = request.auth_context.uid
    org_id = org.id
    facility_id = facility.code if facility else None

    facility_name = facility.name if facility else None

    async def event_stream():
        from app.ai.chat_service import handle_chat_message
        try:
            async for event in handle_chat_message(
                conversation_id=payload.conversation_id,
                user_message=payload.message,
                uid=uid,
                org_id=org_id,
                facility_id=facility_id,
                facility_name=facility_name,
                confirm_action=payload.confirm_action,
                model_provider=payload.model_provider,
                model_name=payload.model_name,
            ):
                yield event.encode()
        except Exception as exc:
            logger.exception("Chat stream error")
            import json
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"
            yield f"event: done\ndata: {json.dumps({'message_id': '', 'text': ''})}\n\n"

    # Django's StreamingHttpResponse with an async generator
    # requires the ASGI server (uvicorn) to handle it properly.
    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


# ---------------------------------------------------------------------------
# Conversations CRUD
# ---------------------------------------------------------------------------

@router.post("/conversations", url_name="ai_create_conversation")
def create_conversation(request, payload: schemas.CreateConversationRequest):
    """Create a new conversation."""
    authorize_request(request, require_firebase=True)
    org, facility = resolve_request_tenant(request)
    uid = request.auth_context.uid

    from app.ai.models import Conversation
    from app.masters.models import AppUser, Facility

    user = AppUser.objects.get(firebase_uid=uid)
    conv = Conversation.objects.create(
        org_id=org.id,
        user=user,
        facility=facility,
        model_provider=payload.model_provider,
        model_name=payload.model_name,
    )
    return success_response(request, _serialize_conversation(conv))


@router.get("/conversations", url_name="ai_list_conversations")
def list_conversations(request):
    """List conversations for the current user."""
    authorize_request(request, require_firebase=True)
    org, facility = resolve_request_tenant(request)
    uid = request.auth_context.uid

    from app.ai.models import Conversation
    from app.masters.models import AppUser

    user = AppUser.objects.get(firebase_uid=uid)
    convs = Conversation.objects.filter(
        org_id=org.id,
        user=user,
        is_active=True,
    ).order_by("-updated_at")[:50]

    return success_response(request, [_serialize_conversation(c) for c in convs])


@router.get("/conversations/{conversation_id}", url_name="ai_get_conversation")
def get_conversation(request, conversation_id: str):
    """Get a conversation with its messages."""
    authorize_request(request, require_firebase=True)
    org, facility = resolve_request_tenant(request)
    uid = request.auth_context.uid

    from app.ai.models import Conversation
    from app.masters.models import AppUser

    user = AppUser.objects.get(firebase_uid=uid)
    conv = Conversation.objects.get(
        id=conversation_id,
        org_id=org.id,
        user=user,
    )
    messages = list(conv.messages.order_by("created_at"))

    data = _serialize_conversation(conv)
    data["messages"] = [_serialize_message(m) for m in messages]
    return success_response(request, data)


@router.delete("/conversations/{conversation_id}", url_name="ai_delete_conversation")
def delete_conversation(request, conversation_id: str):
    """Soft-delete a conversation."""
    authorize_request(request, require_firebase=True)
    org, facility = resolve_request_tenant(request)
    uid = request.auth_context.uid

    from app.ai.models import Conversation
    from app.masters.models import AppUser

    user = AppUser.objects.get(firebase_uid=uid)
    conv = Conversation.objects.get(
        id=conversation_id,
        org_id=org.id,
        user=user,
    )
    conv.is_active = False
    conv.save(update_fields=["is_active", "updated_at"])
    return success_response(request, {"deleted": True})


@router.patch("/conversations/{conversation_id}", url_name="ai_update_conversation")
def update_conversation(request, conversation_id: str, payload: schemas.UpdateConversationRequest):
    """Update conversation settings such as the selected model."""
    authorize_request(request, require_firebase=True)
    org, facility = resolve_request_tenant(request)
    uid = request.auth_context.uid

    from app.ai.models import Conversation
    from app.masters.models import AppUser

    user = AppUser.objects.get(firebase_uid=uid)
    conv = Conversation.objects.get(
        id=conversation_id,
        org_id=org.id,
        user=user,
    )
    conv.model_provider = payload.model_provider
    conv.model_name = payload.model_name
    conv.save(update_fields=["model_provider", "model_name", "updated_at"])
    return success_response(request, _serialize_conversation(conv))


# ---------------------------------------------------------------------------
# Models listing
# ---------------------------------------------------------------------------

@router.get("/models", url_name="ai_list_models")
def list_models(request):
    """List available AI models grouped by provider."""
    authorize_request(request, require_firebase=True)

    from app.ai.chat_service import get_deepagents_models
    from app.ai.llm_providers import ClaudeProvider, OllamaProvider, OpenAIProvider

    results = []

    # deepagents models (static list, always available)
    results.append({
        "provider": "deepagents",
        "models": get_deepagents_models(),
        "is_available": True,
    })

    # Legacy providers
    for provider_name, cls in [("ollama", OllamaProvider), ("openai", OpenAIProvider), ("claude", ClaudeProvider)]:
        provider = cls()
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            models = loop.run_until_complete(provider.list_models())
            results.append({
                "provider": provider_name,
                "models": models,
                "is_available": len(models) > 0,
            })
        except Exception:
            results.append({
                "provider": provider_name,
                "models": [],
                "is_available": False,
            })

    return success_response(request, results)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def _serialize_conversation(conv) -> dict:
    return {
        "id": str(conv.id),
        "title": conv.title,
        "model_provider": conv.model_provider,
        "model_name": conv.model_name,
        "is_active": conv.is_active,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
    }


def _serialize_message(msg) -> dict:
    return {
        "id": str(msg.id),
        "role": msg.role,
        "content": msg.content,
        "components": msg.components,
        "tool_calls": msg.tool_calls,
        "created_at": msg.created_at.isoformat(),
    }
