"""Core AI chat orchestration — handles the LLM tool-calling loop and SSE streaming."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, AsyncIterator, List, Optional
from uuid import UUID

from asgiref.sync import sync_to_async

from app.ai.system_prompt import build_system_prompt
from app.ai.tool_definitions import AUTO_INJECT_PARAMS, MUTATION_TOOLS
from app.ai.tool_executor import execute_tool, summarize_result
from app.core.logging_utils import log_event

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20
PREFETCH_RAG_LIMIT = 5
PREFETCH_RAG_CONTENT_TYPES = ("knowledge", "transaction", "sku", "message")
MAX_PREFETCH_TEXT_CHARS = 500

# Static cloud models supported by deepagents (provider:model format).
STATIC_DEEPAGENTS_MODELS: frozenset[str] = frozenset({
    "anthropic:claude-haiku-4-5",
    "anthropic:claude-sonnet-4-6",
    "anthropic:claude-opus-4-6",
    "openai:gpt-4o",
    "openai:gpt-4o-mini",
    "google:gemini-2.0-flash",
    "google:gemini-2.5-pro",
})


def is_valid_deepagents_model(model: str) -> bool:
    """Return True for known static models or any ollama:* model."""
    return model in STATIC_DEEPAGENTS_MODELS or model.startswith("ollama:")


async def _get_ollama_deepagents_models() -> list[str]:
    """Fetch available Ollama models and return them prefixed with 'ollama:'."""
    import httpx
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [f"ollama:{m['name']}" for m in data.get("models", [])]
    except Exception:
        return []


async def get_deepagents_models() -> list[str]:
    """Return static cloud models plus locally available Ollama models."""
    ollama_models = await _get_ollama_deepagents_models()
    return sorted(STATIC_DEEPAGENTS_MODELS) + ollama_models


_JSON_TYPE_MAP: dict[str, Any] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": List[Any],
    "object": dict,
}


# ---------------------------------------------------------------------------
# SSE event types
# ---------------------------------------------------------------------------

@dataclass
class SSEEvent:
    event: str
    data: dict[str, Any]

    def encode(self) -> str:
        return f"event: {self.event}\ndata: {json.dumps(self.data, default=str)}\n\n"


# ---------------------------------------------------------------------------
# Chat orchestration
# ---------------------------------------------------------------------------

async def handle_chat_message(
    conversation_id: str,
    user_message: str,
    uid: str,
    org_id: str,
    facility_id: str | None = None,
    facility_name: str | None = None,
    model_provider: str | None = None,
    model_name: str | None = None,
    confirm_action: dict | None = None,
) -> AsyncIterator[SSEEvent]:
    """Process a user message and yield SSE events using deepagents."""
    from app.ai.models import Conversation, Message

    execution_log: list[dict[str, Any]] = []
    provider_name = model_provider
    model = model_name
    assistant_message_id: str | None = None
    completion_status = "completed"
    failure: dict[str, str] | None = None
    tool_call_log: list[dict] = []
    components: list[dict] = []

    try:
        # Load conversation
        conversation = await sync_to_async(
            lambda: Conversation.objects.select_related("user", "facility").get(id=conversation_id)
        )()

        provider_name = model_provider or conversation.model_provider
        model = model_name or conversation.model_name
        _append_execution_step(
            execution_log,
            "conversation_loaded",
            model_provider=provider_name,
            model_name=model,
            has_facility=bool(conversation.facility_id),
        )

        # Handle action confirmation (unchanged)
        if confirm_action:
            _append_execution_step(
                execution_log,
                "confirmation_received",
                action=confirm_action["action"],
            )
            yield SSEEvent("tool_call", {"name": confirm_action["action"], "status": "executing"})
            try:
                result = await execute_tool(
                    confirm_action["action"],
                    confirm_action.get("parameters", {}),
                    uid=uid,
                    org_id=org_id,
                    facility_id=facility_id,
                )
                result_text = json.dumps(result, indent=2, default=str)
                _append_execution_step(
                    execution_log,
                    "confirmation_executed",
                    action=confirm_action["action"],
                    result=_summarize_result_for_log(result),
                )
                assistant_msg = await sync_to_async(Message.objects.create)(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content="Action completed successfully.",
                    tool_results=[{"tool": confirm_action["action"], "result": _json_safe(result)}],
                    components=[{
                        "type": "detail_card",
                        "title": f"{confirm_action['action']} Result",
                        "fields": _dict_to_fields(result) if isinstance(result, dict) else [{"label": "Result", "value": result_text}],
                    }],
                )
                assistant_message_id = str(assistant_msg.id)
                yield SSEEvent("tool_result", {"name": confirm_action["action"], "status": "success"})
                yield SSEEvent("components", [{
                    "type": "detail_card",
                    "title": f"{confirm_action['action']} Result",
                    "fields": _dict_to_fields(result) if isinstance(result, dict) else [{"label": "Result", "value": result_text}],
                }])
                yield SSEEvent("done", {"message_id": "", "text": "Action completed successfully."})
                return
            except Exception as exc:
                completion_status = "failed"
                failure = {"type": exc.__class__.__name__, "message": str(exc)}
                _append_execution_step(
                    execution_log,
                    "confirmation_failed",
                    action=confirm_action["action"],
                    error=failure,
                )
                yield SSEEvent("error", {"message": str(exc)})
                yield SSEEvent("done", {"message_id": "", "text": f"Action failed: {exc}"})
                return

        # Save user message
        await sync_to_async(Message.objects.create)(
            conversation=conversation,
            role=Message.Role.USER,
            content=user_message,
        )
        _append_execution_step(execution_log, "user_message_saved", message_chars=len(user_message))

        # Auto-generate title from first message
        msg_count = await sync_to_async(conversation.messages.count)()
        if msg_count == 1:
            title = user_message[:100].strip()
            conversation.title = title
            await sync_to_async(conversation.save)(update_fields=["title", "updated_at"])
            _append_execution_step(execution_log, "conversation_titled", title=title)

        # Prefetch semantic context
        prefetched_context = await _prefetch_semantic_context(user_message, uid, org_id)
        _append_execution_step(
            execution_log,
            "semantic_context_prefetched",
            hit_count=len(prefetched_context or []),
        )

        # Build conversation history (OpenAI-dict format, no system prompt)
        history_messages = await _build_history_messages(conversation, prefetched_context)
        _append_execution_step(
            execution_log,
            "llm_context_built",
            message_count=len(history_messages),
        )

        # Create deepagents agent
        from deepagents import create_deep_agent

        # Prefer the model stored on the conversation when it is a recognised
        # deepagents model; fall back to the env-var default otherwise.
        env_model = os.environ.get("DEEPAGENTS_MODEL", "anthropic:claude-haiku-4-5")
        db_model = conversation.model_name if conversation.model_provider == "deepagents" else None
        deepagents_model = db_model if db_model and is_valid_deepagents_model(db_model) else env_model
        agent = create_deep_agent(
            model=deepagents_model,
            tools=_make_langchain_tools(uid, org_id, facility_id),
            system_prompt=build_system_prompt(org_id, facility_id, facility_name),
        )

        # Stream agent responses
        full_text = ""
        pending_tool_calls: dict[str, dict] = {}  # tool_call_id → {name, args}

        from langchain_core.messages import AIMessageChunk, AIMessage, ToolMessage

        async for chunk, _metadata in agent.astream(
            {"messages": history_messages},
            stream_mode="messages",
        ):
            # Accumulate streamed text tokens
            if isinstance(chunk, AIMessageChunk):
                content = chunk.content
                if isinstance(content, str) and content:
                    full_text += content
                    yield SSEEvent("token", {"text": content})
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text = block.get("text", "")
                            if text:
                                full_text += text
                                yield SSEEvent("token", {"text": text})

                # Track outgoing tool calls
                if chunk.tool_calls:
                    for tc in chunk.tool_calls:
                        if tc.get("id"):
                            pending_tool_calls[tc["id"]] = {
                                "name": tc.get("name", ""),
                                "args": tc.get("args", {}),
                            }
                            yield SSEEvent("tool_call", {
                                "name": tc.get("name", ""),
                                "status": "executing",
                            })

            # Handle tool results
            elif isinstance(chunk, ToolMessage):
                content_str = chunk.content if isinstance(chunk.content, str) else json.dumps(chunk.content, default=str)
                tool_call_id = getattr(chunk, "tool_call_id", "")
                tool_info = pending_tool_calls.pop(tool_call_id, {})
                tool_name = getattr(chunk, "name", "") or tool_info.get("name", "tool")

                # Check for mutation confirmation marker
                try:
                    result_data = json.loads(content_str)
                except (json.JSONDecodeError, TypeError):
                    result_data = None

                if isinstance(result_data, dict) and result_data.get("__needs_confirmation__"):
                    action = result_data["action"]
                    params = result_data.get("parameters", {})
                    yield SSEEvent("tool_call", {
                        "name": action,
                        "status": "needs_confirmation",
                        "args": params,
                    })
                    components.append({
                        "type": "confirmation_dialog",
                        "title": _tool_display_name(action),
                        "description": _describe_mutation(action, params),
                        "action": action,
                        "parameters": params,
                        "requires_confirmation": True,
                    })
                else:
                    tool_call_log.append({
                        "tool": tool_name,
                        "args": _json_safe(tool_info.get("args", {})),
                        "result": _json_safe(result_data or content_str),
                    })
                    yield SSEEvent("tool_result", {
                        "name": tool_name,
                        "status": "success",
                    })

        _append_execution_step(
            execution_log,
            "agent_stream_completed",
            response_chars=len(full_text),
            tool_call_count=len(tool_call_log),
        )

        # Parse final response for structured components
        parsed = _parse_response(full_text)
        if parsed:
            if parsed.get("text"):
                full_text = parsed["text"]
            if parsed.get("components"):
                components.extend(parsed["components"])
            _append_execution_step(
                execution_log,
                "llm_response_parsed",
                component_count=len(parsed.get("components") or []),
            )

        if components:
            yield SSEEvent("components", components)

        # Save assistant message
        assistant_msg = await sync_to_async(Message.objects.create)(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=full_text,
            components=components or None,
            tool_calls=tool_call_log or None,
        )
        assistant_message_id = str(assistant_msg.id)
        _append_execution_step(
            execution_log,
            "assistant_message_saved",
            message_id=assistant_message_id,
            response_chars=len(full_text),
            component_count=len(components),
            tool_call_count=len(tool_call_log),
        )

        await sync_to_async(conversation.save)(update_fields=["updated_at"])

        # Embed Q+A pair for future semantic retrieval (fire-and-forget)
        if full_text and user_message:
            import asyncio
            from app.ai.embeddings import upsert_embedding
            embed_text = f"Q: {user_message}\nA: {full_text}"
            asyncio.create_task(
                upsert_embedding("message", str(assistant_msg.id), org_id, embed_text)
            )

        yield SSEEvent("done", {"message_id": str(assistant_msg.id), "text": full_text})

    except Exception as exc:
        completion_status = "failed"
        failure = {"type": exc.__class__.__name__, "message": str(exc)}
        _append_execution_step(execution_log, "thread_failed", error=failure)
        raise
    finally:
        log_event(
            logger,
            logging.ERROR if completion_status == "failed" else logging.INFO,
            "ai.thread.execution",
            thread_id=conversation_id,
            conversation_id=conversation_id,
            status=completion_status,
            uid=uid,
            org_id=org_id,
            facility_id=facility_id,
            model_provider=provider_name,
            model_name=model,
            assistant_message_id=assistant_message_id,
            execution_log=execution_log,
            error=failure,
        )


# ---------------------------------------------------------------------------
# deepagents tool factory
# ---------------------------------------------------------------------------

def _make_langchain_tools(uid: str, org_id: str, facility_id: str | None) -> list:
    """Build LangChain StructuredTool objects from MCP tool definitions."""
    from pydantic import create_model, Field
    from langchain_core.tools import StructuredTool
    from app.mcp.server import _TOOL_DEFS

    tools = []
    for tool_def in _TOOL_DEFS:
        schema = tool_def.inputSchema
        props = {
            k: v for k, v in schema.get("properties", {}).items()
            if k not in AUTO_INJECT_PARAMS
        }
        required_set = {r for r in schema.get("required", []) if r not in AUTO_INJECT_PARAMS}

        # Build pydantic model for tool arguments
        fields: dict[str, Any] = {}
        for name, prop in props.items():
            py_type = _JSON_TYPE_MAP.get(prop.get("type", ""), Any)
            desc = prop.get("description", "")
            if name in required_set:
                fields[name] = (py_type, Field(..., description=desc))
            else:
                fields[name] = (Optional[py_type], Field(default=None, description=desc))

        ArgsModel = create_model(f"{tool_def.name}_Args", **fields) if fields else _empty_model(tool_def.name)

        # Capture loop variables in closure defaults
        async def _run(
            _tool_name: str = tool_def.name,
            _is_mutation: bool = tool_def.name in MUTATION_TOOLS,
            **kwargs: Any,
        ) -> str:
            if _is_mutation:
                clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
                return json.dumps({
                    "__needs_confirmation__": True,
                    "action": _tool_name,
                    "parameters": clean_kwargs,
                })
            # Strip None values so optional params are not passed to tools
            # that don't handle None (e.g. analytics limit, offset checks).
            clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            try:
                result = await execute_tool(
                    _tool_name, clean_kwargs,
                    uid=uid, org_id=org_id, facility_id=facility_id,
                )
                return summarize_result(result)
            except Exception as exc:
                logger.warning("Tool %s failed: %s", _tool_name, exc)
                return f"Error: {exc}"

        tools.append(StructuredTool(
            name=tool_def.name,
            description=tool_def.description or "",
            args_schema=ArgsModel,
            coroutine=_run,
        ))

    return tools


def _empty_model(tool_name: str):
    from pydantic import BaseModel
    return type(f"{tool_name}_Args", (BaseModel,), {"__annotations__": {}})


# ---------------------------------------------------------------------------
# Message history builder
# ---------------------------------------------------------------------------

async def _build_history_messages(
    conversation,
    prefetched_context: list[dict] | None,
) -> list[dict]:
    """Return conversation history in OpenAI-dict format for deepagents."""
    messages: list[dict] = []

    if prefetched_context is not None:
        messages.append({
            "role": "system",
            "content": _build_prefetched_context_prompt(prefetched_context),
        })

    history = await sync_to_async(
        lambda: list(
            conversation.messages
            .order_by("-created_at")[:MAX_HISTORY_MESSAGES]
        )
    )()
    history.reverse()

    for msg in history:
        entry: dict[str, Any] = {"role": msg.role, "content": msg.content}
        if msg.role == "tool" and msg.tool_results:
            entry["tool_call_id"] = (
                msg.tool_results[0].get("id", "")
                if isinstance(msg.tool_results, list) else ""
            )
        messages.append(entry)

    return messages


# ---------------------------------------------------------------------------
# Semantic context prefetch
# ---------------------------------------------------------------------------

async def _prefetch_semantic_context(
    user_message: str,
    uid: str,
    org_id: str,
) -> list[dict] | None:
    """Fetch semantic context before the first model call for a user message."""
    query = user_message.strip()
    if not query:
        return None

    from app.mcp.tools import wms_semantic_search

    try:
        results = await wms_semantic_search(
            org_id=org_id,
            query=query,
            content_types=list(PREFETCH_RAG_CONTENT_TYPES),
            limit=PREFETCH_RAG_LIMIT,
            uid=uid,
        )
        logger.info("Prefetched semantic context for org=%s hits=%d", org_id, len(results))
        return results
    except Exception:
        logger.exception("Pre-LLM semantic prefetch failed for org=%s", org_id)
        return None


def _build_prefetched_context_prompt(results: list[dict]) -> str:
    intro = (
        "Semantic context has already been prefetched for the current user message "
        "before this first model call. Treat it as supplemental context. Use live "
        "WMS tools for authoritative current-state answers and call "
        "`wms_semantic_search` again only if you need narrower or follow-up retrieval."
    )

    if not results:
        return f"{intro}\n\nPrefetched semantic context result: no relevant matches were found."

    lines = [intro, "", "Prefetched semantic matches:"]
    for idx, item in enumerate(results, start=1):
        text = _truncate_text(str(item.get("text", "")), MAX_PREFETCH_TEXT_CHARS)
        lines.append(
            f"{idx}. type={item.get('type', 'unknown')} "
            f"id={item.get('id', '')} score={item.get('score', '')}"
        )
        lines.append(f"   text={text}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_response(text: str) -> dict | None:
    text = text.strip()
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start) if "```" in text[start:] else len(text)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start) if "```" in text[start:] else len(text)
        text = text[start:end].strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict) and ("text" in data or "components" in data):
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _append_execution_step(execution_log: list[dict[str, Any]], step: str, **data: Any) -> None:
    entry = {"step": step}
    entry.update(data)
    execution_log.append(entry)


def _summarize_result_for_log(result: Any) -> dict[str, Any]:
    if isinstance(result, list):
        return {"type": "list", "count": len(result)}
    if isinstance(result, dict):
        return {"type": "dict", "keys": sorted(str(key) for key in result.keys())[:10]}
    return {"type": type(result).__name__, "preview": _truncate_text(str(result), 200)}


def _tool_display_name(tool_name: str) -> str:
    return tool_name.replace("wms_", "").replace("_", " ").title()


def _describe_mutation(tool_name: str, args: dict) -> str:
    parts = [_tool_display_name(tool_name)]
    if "sku_code" in args:
        parts.append(f"SKU: {args['sku_code']}")
    if "quantity" in args:
        parts.append(f"Qty: {args['quantity']}")
    if "items" in args and isinstance(args["items"], list):
        parts.append(f"{len(args['items'])} item(s)")
    if "reference_number" in args:
        parts.append(f"Ref: {args['reference_number']}")
    return " | ".join(parts)


def _dict_to_fields(d: dict) -> list[dict]:
    fields = []
    for key, value in d.items():
        if isinstance(value, (list, dict)):
            value = json.dumps(value, default=str)
        fields.append({"label": key.replace("_", " ").title(), "value": str(value)})
    return fields


def _truncate_text(text: str, max_chars: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, memoryview):
        return value.tobytes().hex()
    if isinstance(value, bytes):
        return value.hex()
    return value
