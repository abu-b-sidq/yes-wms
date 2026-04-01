"""Core AI chat orchestration — handles the LLM tool-calling loop and SSE streaming."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator

from asgiref.sync import sync_to_async

from app.ai.llm_providers import StreamChunk, get_provider
from app.ai.system_prompt import build_system_prompt
from app.ai.tool_definitions import get_openai_tools
from app.ai.tool_executor import execute_tool, is_mutation_tool, summarize_result

logger = logging.getLogger(__name__)

MAX_TOOL_LOOPS = 5
MAX_HISTORY_MESSAGES = 20


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
    """Process a user message and yield SSE events.

    This is the main orchestration function. It:
    1. Saves the user message
    2. Builds the LLM prompt with tool definitions
    3. Runs the LLM with tool-calling loop
    4. Yields streaming events back to the client
    """
    from app.ai.models import Conversation, Message

    # Load conversation
    conversation = await sync_to_async(
        lambda: Conversation.objects.select_related("user", "facility").get(id=conversation_id)
    )()

    provider_name = model_provider or conversation.model_provider
    model = model_name or conversation.model_name
    provider = get_provider(provider_name)

    # Handle action confirmation
    if confirm_action:
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
            # Save as assistant message
            await sync_to_async(Message.objects.create)(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=f"Action completed successfully.",
                tool_results=[{"tool": confirm_action["action"], "result": result}],
                components=[{
                    "type": "detail_card",
                    "title": f"{confirm_action['action']} Result",
                    "fields": _dict_to_fields(result) if isinstance(result, dict) else [{"label": "Result", "value": result_text}],
                }],
            )
            yield SSEEvent("tool_result", {"name": confirm_action["action"], "status": "success"})
            yield SSEEvent("components", [{
                "type": "detail_card",
                "title": f"{confirm_action['action']} Result",
                "fields": _dict_to_fields(result) if isinstance(result, dict) else [{"label": "Result", "value": result_text}],
            }])
            yield SSEEvent("done", {"message_id": "", "text": "Action completed successfully."})
            return
        except Exception as exc:
            yield SSEEvent("error", {"message": str(exc)})
            yield SSEEvent("done", {"message_id": "", "text": f"Action failed: {exc}"})
            return

    # Save user message
    await sync_to_async(Message.objects.create)(
        conversation=conversation,
        role=Message.Role.USER,
        content=user_message,
    )

    # Auto-generate title from first message
    msg_count = await sync_to_async(conversation.messages.count)()
    if msg_count == 1:
        title = user_message[:100].strip()
        conversation.title = title
        await sync_to_async(conversation.save)(update_fields=["title", "updated_at"])

    # Build message history
    messages = await _build_messages(conversation, org_id, facility_id, facility_name)
    tools = get_openai_tools()

    # LLM tool-calling loop
    full_text = ""
    components: list[dict] = []
    tool_call_log: list[dict] = []

    for loop_idx in range(MAX_TOOL_LOOPS):
        tool_calls_in_response: list[dict] = []
        chunk_text = ""

        async for chunk in provider.chat_completion(messages, tools, model):
            if chunk.delta_text:
                chunk_text += chunk.delta_text
                yield SSEEvent("token", {"text": chunk.delta_text})

            if chunk.tool_calls:
                for tc in chunk.tool_calls:
                    tool_calls_in_response.append({
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                    })

        full_text += chunk_text

        # No tool calls — we're done
        if not tool_calls_in_response:
            break

        # Process tool calls
        messages.append({
            "role": "assistant",
            "content": chunk_text,
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"])},
                }
                for tc in tool_calls_in_response
            ],
        })

        for tc in tool_calls_in_response:
            tool_name = tc["name"]
            tool_args = tc["arguments"]

            # Mutations require confirmation — don't execute, return dialog
            if is_mutation_tool(tool_name):
                yield SSEEvent("tool_call", {"name": tool_name, "status": "needs_confirmation", "args": tool_args})
                confirmation_component = {
                    "type": "confirmation_dialog",
                    "title": _tool_display_name(tool_name),
                    "description": _describe_mutation(tool_name, tool_args),
                    "action": tool_name,
                    "parameters": tool_args,
                    "requires_confirmation": True,
                }
                components.append(confirmation_component)
                # Add a tool result that tells the LLM we're waiting for confirmation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": "PENDING_USER_CONFIRMATION: This action requires user confirmation before execution. A confirmation dialog has been shown to the user.",
                })
                continue

            yield SSEEvent("tool_call", {"name": tool_name, "status": "executing"})
            try:
                result = await execute_tool(
                    tool_name, tool_args,
                    uid=uid, org_id=org_id, facility_id=facility_id,
                )
                result_summary = summarize_result(result)
                tool_call_log.append({"tool": tool_name, "args": tool_args, "result": result})
                yield SSEEvent("tool_result", {"name": tool_name, "status": "success", "count": len(result) if isinstance(result, list) else 1})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_summary,
                })

            except Exception as exc:
                logger.exception("Tool %s failed", tool_name)
                yield SSEEvent("tool_result", {"name": tool_name, "status": "error", "error": str(exc)})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": f"Error: {exc}",
                })

        # If all remaining tool calls were mutations needing confirmation, break
        if all(is_mutation_tool(tc["name"]) for tc in tool_calls_in_response):
            break

    # Parse the final LLM response for structured components
    parsed = _parse_response(full_text)
    if parsed:
        if parsed.get("text"):
            full_text = parsed["text"]
        if parsed.get("components"):
            components.extend(parsed["components"])

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

    # Update conversation timestamp
    await sync_to_async(conversation.save)(update_fields=["updated_at"])

    # Embed the Q+A pair for future semantic retrieval (fire-and-forget)
    if full_text and user_message:
        import asyncio
        from app.ai.embeddings import upsert_embedding
        embed_text = f"Q: {user_message}\nA: {full_text}"
        asyncio.create_task(
            upsert_embedding("message", str(assistant_msg.id), org_id, embed_text)
        )

    yield SSEEvent("done", {"message_id": str(assistant_msg.id), "text": full_text})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _build_messages(
    conversation,
    org_id: str,
    facility_id: str | None,
    facility_name: str | None,
) -> list[dict]:
    """Build the messages array for the LLM from conversation history."""
    system_prompt = build_system_prompt(org_id, facility_id, facility_name)

    messages = [{"role": "system", "content": system_prompt}]

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
            entry["tool_call_id"] = msg.tool_results[0].get("id", "") if isinstance(msg.tool_results, list) else ""
        messages.append(entry)

    return messages


def _parse_response(text: str) -> dict | None:
    """Try to parse the LLM's text as JSON with text + components."""
    text = text.strip()

    # Try to extract JSON from markdown code blocks
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


def _tool_display_name(tool_name: str) -> str:
    """Convert tool name to a human-readable display name."""
    return tool_name.replace("wms_", "").replace("_", " ").title()


def _describe_mutation(tool_name: str, args: dict) -> str:
    """Build a human-readable description of a mutation action."""
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
    """Convert a flat dict to detail_card fields."""
    fields = []
    for key, value in d.items():
        if isinstance(value, (list, dict)):
            value = json.dumps(value, default=str)
        fields.append({"label": key.replace("_", " ").title(), "value": str(value)})
    return fields
