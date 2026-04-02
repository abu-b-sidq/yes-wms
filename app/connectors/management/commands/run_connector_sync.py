"""Management command to run connector sync.

Usage:
    python manage.py run_connector_sync
    python manage.py run_connector_sync --org-id myorg
    python manage.py run_connector_sync --connector-id <uuid>
    python manage.py run_connector_sync --entity SKU --entity INVENTORY
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from app.connectors.models import ConnectorConfig
from app.connectors.sync_orchestrator import run_sync


class Command(BaseCommand):
    help = "Run connector sync for active connectors."

    def add_arguments(self, parser):
        parser.add_argument(
            "--org-id",
            type=str,
            default=None,
            help="Sync connectors for a specific organization only.",
        )
        parser.add_argument(
            "--connector-id",
            type=str,
            default=None,
            help="Sync a specific connector by UUID.",
        )
        parser.add_argument(
            "--entity",
            action="append",
            default=None,
            help="Sync specific entity type(s). Can be repeated.",
        )
        parser.add_argument(
            "--daemon",
            action="store_true",
            default=False,
            help="Deprecated. Continuous scheduling now runs through Celery Beat.",
        )

    def handle(self, *args, **options):
        org_id = options["org_id"]
        connector_id = options["connector_id"]
        entity_types = options["entity"]
        daemon = options["daemon"]

        if daemon:
            raise CommandError(
                "Continuous connector scheduling is handled by Celery Beat. "
                "Run the beat process instead of using --daemon."
            )

        self._run_once(org_id, connector_id, entity_types)

    def _get_connectors(self, org_id, connector_id):
        qs = ConnectorConfig.objects.filter(is_active=True)
        if connector_id:
            qs = qs.filter(id=connector_id)
        if org_id:
            qs = qs.filter(org_id=org_id)
        return list(qs.select_related("org", "facility"))

    def _run_once(self, org_id, connector_id, entity_types):
        connectors = self._get_connectors(org_id, connector_id)
        if not connectors:
            self.stdout.write(self.style.WARNING("No active connectors found."))
            return

        for config in connectors:
            self.stdout.write(
                f"Syncing connector: {config.name} (org={config.org_id})"
            )
            try:
                logs = run_sync(config, entity_types=entity_types)
                for log in logs:
                    self.stdout.write(
                        f"  {log.entity_type}: {log.status} "
                        f"(fetched={log.records_fetched} created={log.records_created} "
                        f"updated={log.records_updated} skipped={log.records_skipped} "
                        f"failed={log.records_failed})"
                    )
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(
                        f"  Error syncing {config.name}: {exc}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Sync complete."))
