"""Conversation and message persistence for AI chat."""
from __future__ import annotations

import uuid

from django.db import models
from pgvector.django import HnswIndex, VectorField

from app.core.base_models import TimestampedModel, UUIDPrimaryKeyMixin


class Conversation(UUIDPrimaryKeyMixin, TimestampedModel):
    """A chat session between a user and the AI assistant."""

    org = models.ForeignKey(
        "app_masters.Organization",
        on_delete=models.CASCADE,
        related_name="ai_conversations",
    )
    user = models.ForeignKey(
        "app_masters.AppUser",
        on_delete=models.CASCADE,
        related_name="ai_conversations",
    )
    facility = models.ForeignKey(
        "app_masters.Facility",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_conversations",
    )
    title = models.CharField(max_length=255, default="New conversation")
    model_provider = models.CharField(
        max_length=32,
        default="ollama",
        help_text="ollama, openai, or claude",
    )
    model_name = models.CharField(
        max_length=128,
        default="llama3.1",
        help_text="Model identifier, e.g. llama3.1, gpt-4o, claude-sonnet-4-20250514",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "-updated_at"]),
            models.Index(fields=["org", "user"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.model_provider}/{self.model_name})"


class Message(UUIDPrimaryKeyMixin, TimestampedModel):
    """A single message in a conversation."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"
        TOOL = "tool", "Tool"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField(blank=True, default="")
    components = models.JSONField(
        null=True,
        blank=True,
        help_text="Structured UI components for the frontend to render",
    )
    tool_calls = models.JSONField(
        null=True,
        blank=True,
        help_text="LLM tool call requests",
    )
    tool_results = models.JSONField(
        null=True,
        blank=True,
        help_text="Tool execution results",
    )
    token_count = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.role}] {self.content[:80]}"


class EmbeddingRecord(models.Model):
    """Stores vector embeddings for semantic search over WMS data."""

    class ContentType(models.TextChoices):
        TRANSACTION = "transaction", "Transaction"
        SKU = "sku", "SKU"
        MESSAGE = "message", "Conversation Message"
        KNOWLEDGE = "knowledge", "Knowledge Base"

    content_type = models.CharField(max_length=20, choices=ContentType.choices, db_index=True)
    object_id = models.CharField(max_length=255)       # UUID or file path + chunk index
    org_id = models.CharField(max_length=255, db_index=True)
    text = models.TextField()                          # Source text that was embedded
    embedding = VectorField(dimensions=768)            # nomic-embed-text output dimension
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ai"
        unique_together = [("content_type", "object_id")]
        indexes = [
            HnswIndex(
                name="emb_hnsw_cosine_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]

    def __str__(self) -> str:
        return f"[{self.content_type}] {self.object_id}"
