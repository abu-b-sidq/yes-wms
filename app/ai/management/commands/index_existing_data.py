"""Management command to backfill embeddings for existing Transactions and SKUs."""
from __future__ import annotations

import json

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Backfill vector embeddings for existing Transactions and SKUs in an org."

    def add_arguments(self, parser):
        parser.add_argument(
            "--org",
            dest="org_id",
            required=True,
            help="Organization ID to backfill.",
        )
        parser.add_argument(
            "--type",
            dest="content_type",
            choices=["transaction", "sku", "all"],
            default="all",
            help="Which content type to backfill (default: all).",
        )

    def handle(self, *args, **options):
        from app.ai.embeddings import upsert_embedding_sync
        from app.masters.models import Organization

        org_id = options["org_id"]
        content_type = options["content_type"]

        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            self.stderr.write(f"Organization '{org_id}' not found.")
            return

        if content_type in ("sku", "all"):
            self._index_skus(org, org_id, upsert_embedding_sync)

        if content_type in ("transaction", "all"):
            self._index_transactions(org, org_id, upsert_embedding_sync)

    def _index_skus(self, org, org_id, upsert_fn):
        from app.masters.models import SKU

        skus = SKU.objects.filter(org=org)
        self.stdout.write(f"Indexing {skus.count()} SKUs...")
        for sku in skus:
            metadata_str = json.dumps(sku.metadata) if sku.metadata else ""
            text = f"SKU: {sku.code} | Name: {sku.name} | UOM: {sku.unit_of_measure} | {metadata_str}".strip(" |")
            upsert_fn("sku", str(sku.id), org_id, text)
            self.stdout.write(f"  SKU {sku.code} — {sku.name}")
        self.stdout.write(self.style.SUCCESS(f"Done indexing {skus.count()} SKUs."))

    def _index_transactions(self, org, org_id, upsert_fn):
        from app.operations.models import Transaction

        txns = Transaction.objects.filter(org=org)
        self.stdout.write(f"Indexing {txns.count()} transactions...")
        for txn in txns:
            parts = [f"[{txn.transaction_type}]"]
            if txn.reference_number:
                parts.append(f"Ref: {txn.reference_number}")
            if txn.notes:
                parts.append(txn.notes)
            parts.append(f"Status: {txn.status}")
            text = " | ".join(parts)
            upsert_fn("transaction", str(txn.id), org_id, text)
            self.stdout.write(f"  {txn.transaction_type} {txn.id} — {txn.status}")
        self.stdout.write(self.style.SUCCESS(f"Done indexing {txns.count()} transactions."))
