"""Embedding service — generate and store vectors for semantic search."""
from __future__ import annotations

import logging
import os

import httpx
from asgiref.sync import sync_to_async
from pgvector.django import CosineDistance

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
_EMBED_URL = f"{OLLAMA_BASE_URL}/api/embeddings"


# ---------------------------------------------------------------------------
# Embed text → vector
# ---------------------------------------------------------------------------

def embed_text_sync(text: str) -> list[float]:
    """Synchronous embedding call — use in signals and management commands."""
    response = httpx.post(
        _EMBED_URL,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["embedding"]


async def embed_text(text: str) -> list[float]:
    """Async embedding call — use in async views and tool executor."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            _EMBED_URL,
            json={"model": EMBED_MODEL, "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]


# ---------------------------------------------------------------------------
# Upsert embedding record
# ---------------------------------------------------------------------------

def upsert_embedding_sync(content_type: str, object_id: str, org_id: str, text: str) -> None:
    """Embed and store synchronously. Safe to call from a background thread."""
    from app.ai.models import EmbeddingRecord
    try:
        vector = embed_text_sync(text)
        EmbeddingRecord.objects.update_or_create(
            content_type=content_type,
            object_id=object_id,
            defaults={"org_id": org_id, "text": text, "embedding": vector},
        )
    except Exception:
        logger.exception("Failed to upsert embedding [%s/%s]", content_type, object_id)


async def upsert_embedding(content_type: str, object_id: str, org_id: str, text: str) -> None:
    """Embed and store asynchronously."""
    from app.ai.models import EmbeddingRecord
    try:
        vector = await embed_text(text)
        await sync_to_async(EmbeddingRecord.objects.update_or_create)(
            content_type=content_type,
            object_id=object_id,
            defaults={"org_id": org_id, "text": text, "embedding": vector},
        )
    except Exception:
        logger.exception("Failed to upsert embedding [%s/%s]", content_type, object_id)


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------

def semantic_search(
    query_vector: list[float],
    org_id: str,
    content_types: list[str],
    limit: int = 5,
) -> list[dict]:
    """Return nearest neighbours by cosine similarity (synchronous, for use in sync_to_async)."""
    from app.ai.models import EmbeddingRecord

    qs = (
        EmbeddingRecord.objects
        .filter(org_id=org_id, content_type__in=content_types)
        .annotate(score=CosineDistance("embedding", query_vector))
        .order_by("score")[:limit]
    )
    return [
        {
            "text": r.text,
            "type": r.content_type,
            "id": r.object_id,
            "score": round(float(1 - r.score), 3),
        }
        for r in qs
    ]
