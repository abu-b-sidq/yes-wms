from __future__ import annotations

from celery import shared_task


@shared_task(name="app.connectors.tasks.run_connector_sync")
def run_connector_sync_task(
    connector_id: str,
    sync_log_ids: list[str] | None = None,
    entity_types: list[str] | None = None,
) -> dict:
    from app.connectors import services

    return services.execute_queued_sync(
        connector_id,
        sync_log_ids=sync_log_ids,
        entity_types=entity_types,
    )


@shared_task(name="app.connectors.tasks.dispatch_due_connector_syncs")
def dispatch_due_connector_syncs() -> dict:
    from app.connectors import services

    return services.dispatch_due_syncs()
