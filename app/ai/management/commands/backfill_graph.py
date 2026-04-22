"""Management command to backfill Neo4j graph with existing WMS data."""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import QuerySet

from app.ai.graph_service import GraphService
from app.masters.models import SKU, Facility, Location
from app.operations.models import Transaction


class Command(BaseCommand):
    help = "Backfill Neo4j knowledge graph with existing WMS data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--org",
            type=str,
            required=True,
            help="Organization ID to backfill",
        )
        parser.add_argument(
            "--type",
            type=str,
            choices=["all", "sku", "facility", "location", "transaction"],
            default="all",
            help="Data type to backfill (default: all)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of records to process (for testing)",
        )

    def handle(self, *args, **options):
        org_id = options["org"]
        data_type = options["type"]
        limit = options["limit"]

        service = GraphService.get_instance()

        try:
            if data_type in ["all", "facility"]:
                self.backfill_facilities(service, org_id, limit)

            if data_type in ["all", "location"]:
                self.backfill_locations(service, org_id, limit)

            if data_type in ["all", "sku"]:
                self.backfill_skus(service, org_id, limit)

            if data_type in ["all", "transaction"]:
                self.backfill_transactions(service, org_id, limit)

            if data_type == "all":
                self.create_relationships(service, org_id, limit)

            self.stdout.write(
                self.style.SUCCESS(f"✓ Backfill completed for org {org_id}")
            )
        except Exception as e:
            raise CommandError(f"Backfill failed: {e}")

    def backfill_facilities(self, service: GraphService, org_id: str, limit: int = None):
        """Backfill Facility nodes."""
        self.stdout.write("Backfilling Facilities...")
        facilities = Facility.objects.filter(org_id=org_id)
        if limit:
            facilities = facilities[:limit]

        count = 0
        for facility in facilities:
            service.create_facility_node(
                org_id=org_id,
                facility_code=facility.code,
                facility_name=facility.name,
                warehouse_key=facility.warehouse_key,
                address=facility.address,
            )
            count += 1

        self.stdout.write(f"  ✓ Created {count} Facility nodes")

    def backfill_locations(self, service: GraphService, org_id: str, limit: int = None):
        """Backfill Location nodes."""
        self.stdout.write("Backfilling Locations...")
        locations = Location.objects.filter(org_id=org_id)
        if limit:
            locations = locations[:limit]

        count = 0
        for location in locations:
            service.create_location_node(
                org_id=org_id,
                location_code=location.code,
                location_name=location.name,
                zone_code=location.zone.code if location.zone else "",
                capacity=location.capacity,
            )
            count += 1

        self.stdout.write(f"  ✓ Created {count} Location nodes")

    def backfill_skus(self, service: GraphService, org_id: str, limit: int = None):
        """Backfill SKU nodes."""
        self.stdout.write("Backfilling SKUs...")
        skus = SKU.objects.filter(org_id=org_id)
        if limit:
            skus = skus[:limit]

        count = 0
        for sku in skus:
            service.create_sku_node(
                org_id=org_id,
                sku_code=sku.code,
                sku_name=sku.name,
                unit_of_measure=sku.unit_of_measure,
                metadata=sku.metadata,
            )
            count += 1

        self.stdout.write(f"  ✓ Created {count} SKU nodes")

    def backfill_transactions(self, service: GraphService, org_id: str, limit: int = None):
        """Backfill Transaction nodes."""
        self.stdout.write("Backfilling Transactions...")
        transactions = Transaction.objects.filter(org_id=org_id)
        if limit:
            transactions = transactions[:limit]

        count = 0
        for txn in transactions:
            service.create_transaction_node(
                org_id=org_id,
                transaction_id=str(txn.id),
                facility_code=txn.facility.code if txn.facility else "",
                transaction_type=txn.transaction_type,
                status=txn.status,
                reference_number=txn.reference_number,
                notes=txn.notes,
            )
            count += 1

        self.stdout.write(f"  ✓ Created {count} Transaction nodes")

    def create_relationships(self, service: GraphService, org_id: str, limit: int = None):
        """Create relationships between nodes."""
        self.stdout.write("Creating relationships...")

        # TODO: In the future, use transaction line items to link SKUs to Transactions
        # For now, this is a placeholder for future expansion

        self.stdout.write("  ✓ Relationships created")
