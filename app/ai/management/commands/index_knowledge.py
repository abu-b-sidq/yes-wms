"""Management command to embed knowledge base markdown files into the vector store."""
from __future__ import annotations

import os
from pathlib import Path

from django.core.management.base import BaseCommand

KNOWLEDGE_DIR = Path(__file__).resolve().parents[4] / "knowledge"
CHUNK_SIZE = 500  # approximate characters per chunk


def _split_chunks(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text into overlapping chunks at paragraph boundaries."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 > size and current:
            chunks.append(current.strip())
            # 50-char overlap: keep last sentence of current chunk
            overlap = current[-100:].strip()
            current = overlap + "\n\n" + para
        else:
            current = (current + "\n\n" + para).strip() if current else para
    if current:
        chunks.append(current.strip())
    return chunks or [text[:size]]


class Command(BaseCommand):
    help = "Embed knowledge base markdown files for all orgs' semantic search."

    def add_arguments(self, parser):
        parser.add_argument(
            "--org",
            dest="org_id",
            required=True,
            help="Organization ID to associate knowledge embeddings with.",
        )
        parser.add_argument(
            "--dir",
            dest="knowledge_dir",
            default=str(KNOWLEDGE_DIR),
            help="Path to directory containing markdown files.",
        )

    def handle(self, *args, **options):
        from app.ai.embeddings import upsert_embedding_sync

        org_id = options["org_id"]
        knowledge_dir = Path(options["knowledge_dir"])

        if not knowledge_dir.exists():
            self.stderr.write(f"Knowledge directory not found: {knowledge_dir}")
            return

        md_files = list(knowledge_dir.glob("*.md"))
        if not md_files:
            self.stderr.write(f"No .md files found in {knowledge_dir}")
            return

        self.stdout.write(f"Indexing {len(md_files)} file(s) for org '{org_id}'...")
        total_chunks = 0

        for md_file in md_files:
            text = md_file.read_text(encoding="utf-8")
            chunks = _split_chunks(text)
            filename = md_file.stem

            for i, chunk in enumerate(chunks):
                object_id = f"{filename}#{i}"
                upsert_embedding_sync("knowledge", object_id, org_id, chunk)
                total_chunks += 1
                self.stdout.write(f"  {filename}#{i} ({len(chunk)} chars)")

        self.stdout.write(self.style.SUCCESS(f"Done. Indexed {total_chunks} chunk(s) from {len(md_files)} file(s)."))
