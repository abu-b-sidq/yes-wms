"""Signals for embedding operations data for semantic search."""
from __future__ import annotations

import threading

from django.db.models.signals import post_save
from django.dispatch import receiver

from app.operations.models import Transaction


@receiver(post_save, sender=Transaction)
def embed_transaction(sender, instance, **kwargs):
    """Asynchronously embed a Transaction for semantic search."""
    parts = [f"[{instance.transaction_type}]"]
    if instance.reference_number:
        parts.append(f"Ref: {instance.reference_number}")
    if instance.notes:
        parts.append(instance.notes)
    parts.append(f"Status: {instance.status}")
    text = " | ".join(parts)

    org_id = str(instance.org_id)
    object_id = str(instance.id)

    def _run():
        from app.ai.embeddings import upsert_embedding_sync
        upsert_embedding_sync("transaction", object_id, org_id, text)

    threading.Thread(target=_run, daemon=True).start()


@receiver(post_save, sender=Transaction)
def create_transaction_graph_node(sender, instance, **kwargs):
    """Asynchronously create Transaction node in knowledge graph."""
    def _run():
        from app.ai.graph_service import GraphService
        service = GraphService.get_instance()
        service.create_transaction_node(
            org_id=str(instance.org_id),
            transaction_id=str(instance.id),
            facility_code=instance.facility.code if instance.facility else "",
            transaction_type=instance.transaction_type,
            status=instance.status,
            reference_number=instance.reference_number,
            notes=instance.notes,
        )

    threading.Thread(target=_run, daemon=True).start()
