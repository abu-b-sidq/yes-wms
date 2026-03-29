"""LLM provider abstraction — Ollama (default), OpenAI, and Claude."""
from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

import httpx

logger = logging.getLogger(__name__)


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


# ---------------------------------------------------------------------------
# Ollama (self-hosted, default)
# ---------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

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

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload
            ) as response:
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

        # Convert from OpenAI format to Anthropic format
        system_text = ""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text += msg["content"] + "\n"
            elif msg["role"] == "tool":
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": msg["content"],
                    }],
                })
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

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
# Factory
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
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
    return os.getenv("AI_DEFAULT_MODEL", "llama3.1")
