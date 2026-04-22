"""Management command to index knowledge base files into Neo4j knowledge graph."""
from __future__ import annotations

import uuid
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

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
            # 100-char overlap: keep last sentences of current chunk
            overlap = current[-100:].strip()
            current = overlap + "\n\n" + para
        else:
            current = (current + "\n\n" + para).strip() if current else para
    if current:
        chunks.append(current.strip())
    return chunks or [text[:size]]


class Command(BaseCommand):
    help = "Index knowledge base markdown files into Neo4j knowledge graph"

    def add_arguments(self, parser):
        parser.add_argument(
            "--org",
            dest="org_id",
            required=True,
            help="Organization ID to associate knowledge items with",
        )
        parser.add_argument(
            "--dir",
            dest="knowledge_dir",
            default=str(KNOWLEDGE_DIR),
            help="Path to directory containing markdown files (default: ./knowledge)",
        )
        parser.add_argument(
            "--category",
            dest="category",
            default="procedure",
            choices=["procedure", "guide", "policy", "faq", "other"],
            help="Category for knowledge items (default: procedure)",
        )
        parser.add_argument(
            "--auto-relate",
            action="store_true",
            help="Automatically create RELATES_TO relationships to existing SKUs/Locations/Facilities",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be indexed without actually creating nodes",
        )

    def handle(self, *args, **options):
        from app.ai.graph_service import GraphService

        org_id = options["org_id"]
        knowledge_dir = Path(options["knowledge_dir"])
        category = options["category"]
        auto_relate = options["auto_relate"]
        dry_run = options["dry_run"]

        # Validate knowledge directory
        if not knowledge_dir.exists():
            raise CommandError(f"Knowledge directory not found: {knowledge_dir}")

        # Find markdown files
        md_files = sorted(knowledge_dir.glob("*.md"))
        if not md_files:
            raise CommandError(f"No .md files found in {knowledge_dir}")

        self.stdout.write(
            self.style.WARNING(
                f"Indexing knowledge from {len(md_files)} file(s) into Neo4j\n"
                f"Organization: {org_id}\n"
                f"Category: {category}\n"
                f"Auto-relate: {auto_relate}\n"
                f"Dry run: {dry_run}\n"
            )
        )

        if not dry_run:
            service = GraphService.get_instance()

        total_chunks = 0
        total_files = 0

        for md_file in md_files:
            try:
                text = md_file.read_text(encoding="utf-8")
                chunks = _split_chunks(text)
                filename = md_file.stem
                total_files += 1

                self.stdout.write(f"\n📄 {filename}")

                for i, chunk in enumerate(chunks):
                    # Generate unique ID for this knowledge chunk
                    item_id = f"{filename}-chunk-{i}"
                    title = f"{filename} (Part {i+1} of {len(chunks)})"

                    if dry_run:
                        self.stdout.write(
                            f"  [DRY RUN] Would create: {item_id}"
                        )
                        self.stdout.write(
                            f"           Title: {title[:60]}..."
                        )
                        self.stdout.write(
                            f"           Content: {len(chunk)} chars\n"
                        )
                    else:
                        # Create knowledge item node
                        success = service.create_knowledge_item_node(
                            org_id=org_id,
                            item_id=item_id,
                            title=title,
                            content=chunk,
                            category=category,
                        )

                        if success:
                            self.stdout.write(f"  ✓ Created: {item_id}")

                            # Auto-relate to matching entities
                            if auto_relate:
                                self._create_relationships(
                                    service, org_id, item_id, chunk
                                )
                        else:
                            self.stdout.write(
                                self.style.ERROR(f"  ✗ Failed: {item_id}")
                            )

                    total_chunks += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  Error processing {md_file.name}: {e}"
                    )
                )

        # Summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Completed: Indexed {total_chunks} chunk(s) from {total_files} file(s)"
            )
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING("(This was a DRY RUN - no data was created)")
            )

    def _create_relationships(
        self, service: GraphService, org_id: str, item_id: str, content: str
    ) -> None:
        """Auto-create RELATES_TO relationships for mentioned entities."""
        from app.masters.models import SKU, Location, Facility

        # Extract potential SKU codes (uppercase codes like "ABC123", "SKU-001", etc.)
        import re

        # Look for SKU codes: 3-20 char alphanumeric with optional hyphens
        sku_pattern = r"\b([A-Z0-9]{3,20}(?:-[A-Z0-9]+)*)\b"
        potential_skus = set(re.findall(sku_pattern, content))

        for sku_code in potential_skus:
            # Verify it's a real SKU in the database
            if SKU.objects.filter(org_id=org_id, code=sku_code).exists():
                success = service.create_relates_to_relationship(
                    org_id=org_id,
                    knowledge_id=item_id,
                    target_type="SKU",
                    target_code=sku_code,
                )
                if success:
                    self.stdout.write(f"    → Linked to SKU: {sku_code}")

        # Look for location codes (mentioned as "LOCATION:", "LOC:", etc.)
        location_pattern = r"(?:location|loc|zone)[\s:]+([A-Z0-9\-]+)"
        potential_locations = set(re.findall(location_pattern, content, re.IGNORECASE))

        for loc_code in potential_locations:
            if Location.objects.filter(org_id=org_id, code=loc_code).exists():
                success = service.create_relates_to_relationship(
                    org_id=org_id,
                    knowledge_id=item_id,
                    target_type="Location",
                    target_code=loc_code,
                )
                if success:
                    self.stdout.write(f"    → Linked to Location: {loc_code}")

        # Look for facility codes (mentioned as "FACILITY:", "WAREHOUSE:", etc.)
        facility_pattern = r"(?:facility|warehouse|wh|fac)[\s:]+([A-Z0-9\-]+)"
        potential_facilities = set(
            re.findall(facility_pattern, content, re.IGNORECASE)
        )

        for fac_code in potential_facilities:
            if Facility.objects.filter(org_id=org_id, code=fac_code).exists():
                success = service.create_relates_to_relationship(
                    org_id=org_id,
                    knowledge_id=item_id,
                    target_type="Facility",
                    target_code=fac_code,
                )
                if success:
                    self.stdout.write(f"    → Linked to Facility: {fac_code}")
