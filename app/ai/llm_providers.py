"""LLM provider abstraction — Ollama (default), OpenAI, and Claude."""
from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

import httpx

from app.core.logging_utils import log_event

logger = logging.getLogger(__name__)
prompt_logger = logging.getLogger("app.ai.llm_prompts")


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class StreamChunk:
    """A single chunk from a streaming LLM response."""
    delta_text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None


# ---------------------------------------------------------------------------
# Abstract provider
# ---------------------------------------------------------------------------

class LLMProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str,
    ) -> AsyncIterator[StreamChunk]:
        """Yield streaming chunks from the LLM."""
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Return available model names."""
        ...


def _extract_tool_names(tools: list[dict[str, Any]]) -> list[str]:
    tool_names: list[str] = []
    for tool in tools:
        function = tool.get("function", {}) if isinstance(tool, dict) else {}
        name = function.get("name")
        if isinstance(name, str) and name:
            tool_names.append(name)
    return tool_names


def _log_prompt_request(
    *,
    provider_name: str,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    system: str | None = None,
) -> None:
    event_data: dict[str, Any] = {
        "provider": provider_name,
        "model": model,
        "message_count": len(messages),
        "tool_names": _extract_tool_names(tools),
        "messages": messages,
    }
    if system is not None:
        event_data["system"] = system

    log_event(prompt_logger, logging.INFO, "ai.prompt", **event_data)


# ---------------------------------------------------------------------------
# Ollama (self-hosted, default)
# ---------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    _tool_support_cache: dict[str, bool] = {}

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    async def _supports_tools(self, model: str) -> bool:
        """Check if an Ollama model supports tool/function calling."""
        if model in self._tool_support_cache:
            return self._tool_support_cache[model]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/show", json={"model": model}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # Ollama exposes a model's template; models with tool support
                    # include a `.Tools` directive in their template.
                    template = data.get("template", "")
                    supported = ".Tools" in template
                    self._tool_support_cache[model] = supported
                    return supported
        except Exception:
            logger.debug("Could not check tool support for model %s, assuming supported", model)
        self._tool_support_cache[model] = True
        return True

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str,
    ) -> AsyncIterator[StreamChunk]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools

        logger.debug("OllamaProvider.chat_completion model=%s tools=%d", model, len(tools))

        if tools and not await self._supports_tools(model):
            logger.warning("Model %s does not support tools — sending without tools", model)
            payload.pop("tools", None)

        _log_prompt_request(
            provider_name="ollama",
            model=model,
            messages=messages,
            tools=payload.get("tools", []),
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload
            ) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    logger.error(
                        "Ollama /api/chat error %s — model=%s body=%s",
                        response.status_code, model, body.decode(errors="replace"),
                    )
                    response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    chunk = StreamChunk()

                    msg = data.get("message", {})
                    if msg.get("content"):
                        chunk.delta_text = msg["content"]

                    if msg.get("tool_calls"):
                        for tc in msg["tool_calls"]:
                            func = tc.get("function", {})
                            chunk.tool_calls.append(ToolCall(
                                id=func.get("name", ""),
                                name=func.get("name", ""),
                                arguments=func.get("arguments", {}),
                            ))

                    if data.get("done"):
                        chunk.finish_reason = "stop"

                    yield chunk

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            logger.warning("Could not connect to Ollama at %s", self.base_url)
            return []


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str,
    ) -> AsyncIterator[StreamChunk]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools

        _log_prompt_request(
            provider_name="openai",
            model=model,
            messages=messages,
            tools=tools,
        )

        # Accumulate partial tool calls across chunks
        pending_tool_calls: dict[int, dict] = {}

        stream = await client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            sc = StreamChunk()

            if delta.content:
                sc.delta_text = delta.content

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in pending_tool_calls:
                        pending_tool_calls[idx] = {
                            "id": tc_delta.id or "",
                            "name": "",
                            "arguments": "",
                        }
                    if tc_delta.function:
                        if tc_delta.function.name:
                            pending_tool_calls[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            pending_tool_calls[idx]["arguments"] += tc_delta.function.arguments

            finish = chunk.choices[0].finish_reason if chunk.choices else None
            if finish:
                sc.finish_reason = finish
                # Emit accumulated tool calls on finish
                if finish == "tool_calls" and pending_tool_calls:
                    for tc_data in pending_tool_calls.values():
                        try:
                            args = json.loads(tc_data["arguments"])
                        except json.JSONDecodeError:
                            args = {}
                        sc.tool_calls.append(ToolCall(
                            id=tc_data["id"],
                            name=tc_data["name"],
                            arguments=args,
                        ))
                    pending_tool_calls.clear()

            yield sc

    async def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            models = await client.models.list()
            return sorted(
                m.id for m in models.data
                if m.id.startswith(("gpt-4", "gpt-3.5"))
            )
        except Exception:
            logger.warning("Could not list OpenAI models")
            return []


# ---------------------------------------------------------------------------
# Claude (Anthropic)
# ---------------------------------------------------------------------------

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str,
    ) -> AsyncIterator[StreamChunk]:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)

        # Anthropic expects assistant tool requests as `tool_use` blocks and
        # the matching tool results grouped into the next user message.
        system_text, anthropic_messages = _to_anthropic_messages(messages)

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": 4096,
            "messages": anthropic_messages,
        }
        if system_text.strip():
            kwargs["system"] = system_text.strip()
        if tools:
            from app.ai.tool_definitions import get_anthropic_tools
            kwargs["tools"] = get_anthropic_tools()

        _log_prompt_request(
            provider_name="claude",
            model=model,
            messages=anthropic_messages,
            tools=tools,
            system=system_text.strip() or None,
        )

        async with client.messages.stream(**kwargs) as stream:
            current_tool_id = ""
            current_tool_name = ""
            current_tool_args = ""

            async for event in stream:
                sc = StreamChunk()

                if event.type == "content_block_start":
                    if hasattr(event.content_block, "type") and event.content_block.type == "tool_use":
                        current_tool_id = event.content_block.id
                        current_tool_name = event.content_block.name
                        current_tool_args = ""
                elif event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        sc.delta_text = event.delta.text
                    elif hasattr(event.delta, "partial_json"):
                        current_tool_args += event.delta.partial_json
                elif event.type == "content_block_stop":
                    if current_tool_name:
                        try:
                            args = json.loads(current_tool_args) if current_tool_args else {}
                        except json.JSONDecodeError:
                            args = {}
                        sc.tool_calls.append(ToolCall(
                            id=current_tool_id,
                            name=current_tool_name,
                            arguments=args,
                        ))
                        current_tool_name = ""
                        current_tool_args = ""
                elif event.type == "message_stop":
                    sc.finish_reason = "stop"

                yield sc

    async def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        return [
            "claude-sonnet-4-20250514",
            "claude-haiku-4-5-20251001",
            "claude-opus-4-20250514",
        ]


# ---------------------------------------------------------------------------
# Langgraph DeepAgent
# ---------------------------------------------------------------------------

class DeepAgentProvider(LLMProvider):
    """Provider using Langgraph's deepagent framework for advanced agentic behavior.

    This implementation uses Claude with Langgraph's tool-use abstractions
    to provide enhanced agentic capabilities over the standard Claude provider.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required for DeepAgent")

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str,
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion using Claude through Langgraph abstractions.

        Uses the same streaming approach as ClaudeProvider but leverages
        Langgraph's deepagent infrastructure for potential future enhancements.
        """
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)

        # Convert to Anthropic message format
        system_text, anthropic_messages = _to_anthropic_messages(messages)

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": 4096,
            "messages": anthropic_messages,
        }
        if system_text.strip():
            kwargs["system"] = system_text.strip()
        if tools:
            from app.ai.tool_definitions import get_anthropic_tools
            kwargs["tools"] = get_anthropic_tools()

        logger.debug("DeepAgentProvider.chat_completion model=%s tools=%d", model, len(tools or []))

        _log_prompt_request(
            provider_name="deepagent",
            model=model,
            messages=anthropic_messages,
            tools=tools,
            system=system_text.strip() or None,
        )

        async with client.messages.stream(**kwargs) as stream:
            current_tool_id = ""
            current_tool_name = ""
            current_tool_args = ""

            async for event in stream:
                sc = StreamChunk()

                if event.type == "content_block_start":
                    if hasattr(event.content_block, "type") and event.content_block.type == "tool_use":
                        current_tool_id = event.content_block.id
                        current_tool_name = event.content_block.name
                        current_tool_args = ""
                elif event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        sc.delta_text = event.delta.text
                    elif hasattr(event.delta, "partial_json"):
                        current_tool_args += event.delta.partial_json
                elif event.type == "content_block_stop":
                    if current_tool_name:
                        try:
                            args = json.loads(current_tool_args) if current_tool_args else {}
                        except json.JSONDecodeError:
                            args = {}
                        sc.tool_calls.append(ToolCall(
                            id=current_tool_id,
                            name=current_tool_name,
                            arguments=args,
                        ))
                        current_tool_name = ""
                        current_tool_args = ""
                elif event.type == "message_stop":
                    sc.finish_reason = "stop"

                yield sc

    async def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        return [
            "claude-sonnet-4-20250514",
            "claude-haiku-4-5-20251001",
            "claude-opus-4-20250514",
        ]


# ---------------------------------------------------------------------------
# Claude helpers
# ---------------------------------------------------------------------------

def _parse_tool_arguments(raw_arguments: Any) -> dict[str, Any]:
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if isinstance(raw_arguments, str):
        try:
            parsed = json.loads(raw_arguments)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _to_anthropic_messages(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """Convert OpenAI-style messages into Anthropic message content blocks."""
    system_parts: list[str] = []
    anthropic_messages: list[dict[str, Any]] = []
    pending_tool_results: list[dict[str, Any]] = []

    def flush_pending_tool_results() -> None:
        if not pending_tool_results:
            return
        anthropic_messages.append({
            "role": "user",
            "content": pending_tool_results.copy(),
        })
        pending_tool_results.clear()

    for msg in messages:
        role = msg.get("role", "")
        content = str(msg.get("content", ""))

        if role == "system":
            if content:
                system_parts.append(content)
            continue

        if role == "tool":
            pending_tool_results.append({
                "type": "tool_result",
                "tool_use_id": msg.get("tool_call_id", ""),
                "content": content,
            })
            continue

        flush_pending_tool_results()

        if role == "assistant" and msg.get("tool_calls"):
            content_blocks: list[dict[str, Any]] = []
            if content:
                content_blocks.append({
                    "type": "text",
                    "text": content,
                })

            for tool_call in msg.get("tool_calls", []):
                function = tool_call.get("function", {})
                content_blocks.append({
                    "type": "tool_use",
                    "id": tool_call.get("id", ""),
                    "name": function.get("name", ""),
                    "input": _parse_tool_arguments(function.get("arguments", {})),
                })

            anthropic_messages.append({
                "role": "assistant",
                "content": content_blocks,
            })
            continue

        anthropic_messages.append({
            "role": role,
            "content": content,
        })

    flush_pending_tool_results()

    return "\n".join(system_parts).strip(), anthropic_messages


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "deepagent": DeepAgentProvider,
}


def get_provider(provider_name: str) -> LLMProvider:
    """Instantiate an LLM provider by name."""
    cls = _PROVIDERS.get(provider_name)
    if cls is None:
        raise ValueError(f"Unknown LLM provider: {provider_name}. Available: {list(_PROVIDERS)}")
    return cls()


def get_default_provider() -> str:
    return os.getenv("AI_DEFAULT_PROVIDER", "ollama")


def get_default_model() -> str:
    return os.getenv("AI_DEFAULT_MODEL", "qwen2.5:7b")
