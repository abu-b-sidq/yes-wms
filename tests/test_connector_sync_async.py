from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone

from app.connectors import services
from app.connectors.enums import ConnectorType, SyncEntityType, SyncStatus
from app.connectors.models import ConnectorConfig, SyncLog


pytestmark = pytest.mark.django_db


@pytest.fixture
def connector(org, facility):
    return ConnectorConfig.objects.create(
        org=org,
        name="StockOne Primary",
        connector_type=ConnectorType.STOCKONE,
        facility=facility,
        config={"base_url": "https://stockone.example.test"},
        sync_interval_minutes=60,
        enabled_entities=[SyncEntityType.SKU, SyncEntityType.INVENTORY],
    )


def test_trigger_sync_endpoint_queues_background_task(
    client,
    org,
    connector,
    api_headers,
    monkeypatch,
):
    captured: dict[str, object] = {}

    def fake_delay(connector_id, sync_log_ids, entity_types):
        captured["connector_id"] = connector_id
        captured["sync_log_ids"] = sync_log_ids
        captured["entity_types"] = entity_types
        return SimpleNamespace(id="task-123")

    monkeypatch.setattr(
        "app.connectors.tasks.run_connector_sync_task.delay",
        fake_delay,
    )

    response = client.post(
        f"/api/v1/connectors/{connector.id}/sync",
        data={"entity_types": [SyncEntityType.SKU]},
        content_type="application/json",
        **api_headers(org_id=org.id, facility_id=None),
    )

    assert response.status_code == 202
    body = response.json()

    assert body["success"] is True
    assert body["meta"]["task_id"] == "task-123"
    assert len(body["data"]) == 1
    assert body["data"][0]["entity_type"] == SyncEntityType.SKU
    assert body["data"][0]["status"] == SyncStatus.PENDING
    assert captured == {
        "connector_id": str(connector.id),
        "sync_log_ids": [body["data"][0]["id"]],
        "entity_types": [SyncEntityType.SKU],
    }


def test_execute_queued_sync_reuses_pending_logs(connector, monkeypatch):
    pending_log = SyncLog.objects.create(
        connector=connector,
        org=connector.org,
        entity_type=SyncEntityType.SKU,
        status=SyncStatus.PENDING,
    )
    captured: dict[str, object] = {}

    def fake_run_sync(config, entity_types=None, sync_logs_by_entity=None):
        captured["config_id"] = str(config.id)
        captured["entity_types"] = entity_types
        captured["sync_log_ids"] = {
            entity_type: str(log.id)
            for entity_type, log in (sync_logs_by_entity or {}).items()
        }
        pending_log.status = SyncStatus.COMPLETED
        pending_log.started_at = timezone.now()
        pending_log.completed_at = pending_log.started_at
        return [pending_log]

    monkeypatch.setattr("app.connectors.services.run_sync", fake_run_sync)

    result = services.execute_queued_sync(
        str(connector.id),
        sync_log_ids=[str(pending_log.id)],
        entity_types=[SyncEntityType.SKU],
    )

    assert result == {
        "connector_id": str(connector.id),
        "entity_types": [SyncEntityType.SKU],
        "log_ids": [str(pending_log.id)],
    }
    assert captured == {
        "config_id": str(connector.id),
        "entity_types": [SyncEntityType.SKU],
        "sync_log_ids": {SyncEntityType.SKU: str(pending_log.id)},
    }


def test_dispatch_due_syncs_queues_only_due_idle_connectors(
    org,
    facility,
    monkeypatch,
):
    now = timezone.now()
    due_connector = ConnectorConfig.objects.create(
        org=org,
        name="Due Connector",
        connector_type=ConnectorType.STOCKONE,
        facility=facility,
        config={"base_url": "https://stockone.example.test"},
        sync_interval_minutes=60,
        enabled_entities=[SyncEntityType.SKU],
        last_synced_at=now - timedelta(minutes=61),
    )
    ConnectorConfig.objects.create(
        org=org,
        name="Not Due Connector",
        connector_type=ConnectorType.STOCKONE,
        facility=facility,
        config={"base_url": "https://stockone.example.test"},
        sync_interval_minutes=60,
        enabled_entities=[SyncEntityType.SKU],
        last_synced_at=now - timedelta(minutes=30),
    )
    running_connector = ConnectorConfig.objects.create(
        org=org,
        name="Running Connector",
        connector_type=ConnectorType.STOCKONE,
        facility=facility,
        config={"base_url": "https://stockone.example.test"},
        sync_interval_minutes=60,
        enabled_entities=[SyncEntityType.SKU],
        last_synced_at=now - timedelta(minutes=61),
    )
    SyncLog.objects.create(
        connector=running_connector,
        org=org,
        entity_type=SyncEntityType.SKU,
        status=SyncStatus.RUNNING,
        started_at=now,
    )

    queued_calls: list[dict[str, object]] = []

    def fake_delay(connector_id, sync_log_ids, entity_types):
        queued_calls.append(
            {
                "connector_id": connector_id,
                "sync_log_ids": sync_log_ids,
                "entity_types": entity_types,
            }
        )
        return SimpleNamespace(id=f"task-{len(queued_calls)}")

    monkeypatch.setattr(
        "app.connectors.tasks.run_connector_sync_task.delay",
        fake_delay,
    )

    result = services.dispatch_due_syncs()

    assert result["queued"] == 1
    assert result["skipped"] == 2
    assert result["errors"] == []
    assert result["task_ids"] == ["task-1"]
    assert queued_calls == [
        {
            "connector_id": str(due_connector.id),
            "sync_log_ids": [
                str(log_id)
                for log_id in SyncLog.objects.filter(connector=due_connector)
                .order_by("created_at")
                .values_list("id", flat=True)
            ],
            "entity_types": [SyncEntityType.SKU],
        }
    ]
