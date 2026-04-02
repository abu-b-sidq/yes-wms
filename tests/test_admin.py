import uuid
from types import SimpleNamespace

import pytest
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse

from app.connectors.enums import ConnectorType, SyncEntityType, SyncStatus
from app.connectors.models import ConnectorConfig, ExternalEntityMapping, SyncLog
from app.documents.models import TransactionDocumentConfig
from app.inventory.models import InventoryBalance, InventoryLedger
from app.masters.models import (
    AppUser,
    Organization,
    Role,
    UserOrgMembership,
)
from app.operations.models import Transaction


pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user(db):
    user_model = get_user_model()
    return user_model.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="admin-pass-123",
    )


@pytest.fixture
def connector(org, facility):
    return ConnectorConfig.objects.create(
        org=org,
        name="StockOne Primary",
        connector_type=ConnectorType.STOCKONE,
        facility=facility,
        config={"base_url": "https://stockone.example.test"},
        sync_interval_minutes=60,
        enabled_entities=[SyncEntityType.SKU],
    )


def test_admin_login_page_is_available(client):
    response = client.get(reverse("admin:login"))

    assert response.status_code == 200
    assert b"csrfmiddlewaretoken" in response.content


def test_admin_index_redirects_anonymous_users_to_login(client):
    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert reverse("admin:login") in response.url


def test_admin_index_loads_for_superuser(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("admin:index"))

    assert response.status_code == 200
    assert b"WMS Masters" in response.content
    assert b"WMS Operations" in response.content
    assert b"WMS Inventory" in response.content
    assert b"WMS Documents" in response.content
    assert b"WMS Connectors" in response.content


def test_admin_registers_key_domain_models():
    expected_models = {
        AppUser,
        ConnectorConfig,
        ExternalEntityMapping,
        InventoryBalance,
        InventoryLedger,
        Organization,
        Role,
        SyncLog,
        Transaction,
        TransactionDocumentConfig,
        UserOrgMembership,
    }

    assert expected_models <= set(site._registry)


def test_connector_admin_changelist_shows_dispatch_button(client, admin_user, connector):
    client.force_login(admin_user)

    response = client.get(reverse("admin:connectors_connectorconfig_changelist"))

    assert response.status_code == 200
    assert b"Dispatch due syncs now" in response.content


def test_connector_admin_queue_sync_action_queues_each_selected_connector(
    client,
    admin_user,
    org,
    facility,
    monkeypatch,
):
    connector_one = ConnectorConfig.objects.create(
        org=org,
        name="Connector One",
        connector_type=ConnectorType.STOCKONE,
        facility=facility,
        config={"base_url": "https://stockone.example.test"},
        enabled_entities=[SyncEntityType.SKU],
    )
    connector_two = ConnectorConfig.objects.create(
        org=org,
        name="Connector Two",
        connector_type=ConnectorType.STOCKONE,
        facility=facility,
        config={"base_url": "https://stockone.example.test"},
        enabled_entities=[SyncEntityType.INVENTORY],
    )
    captured: list[tuple[str, str]] = []

    def fake_trigger_sync(target_org, connector_id):
        captured.append((target_org.id, str(connector_id)))
        return SimpleNamespace(logs=[], task_id="task-123")

    monkeypatch.setattr("app.connectors.admin.services.trigger_sync", fake_trigger_sync)
    client.force_login(admin_user)

    response = client.post(
        reverse("admin:connectors_connectorconfig_changelist"),
        {
            "action": "queue_sync_now",
            ACTION_CHECKBOX_NAME: [str(connector_one.id), str(connector_two.id)],
        },
        follow=True,
    )

    assert response.status_code == 200
    assert set(captured) == {
        (org.id, str(connector_one.id)),
        (org.id, str(connector_two.id)),
    }
    assert b"Queued sync for 2 connector(s)." in response.content


def test_connector_admin_queue_sync_action_reports_failures_without_aborting(
    client,
    admin_user,
    org,
    facility,
    monkeypatch,
):
    connector_one = ConnectorConfig.objects.create(
        org=org,
        name="Connector One",
        connector_type=ConnectorType.STOCKONE,
        facility=facility,
        config={"base_url": "https://stockone.example.test"},
        enabled_entities=[SyncEntityType.SKU],
    )
    connector_two = ConnectorConfig.objects.create(
        org=org,
        name="Connector Two",
        connector_type=ConnectorType.STOCKONE,
        facility=facility,
        config={"base_url": "https://stockone.example.test"},
        enabled_entities=[SyncEntityType.INVENTORY],
    )
    captured: list[str] = []

    def fake_trigger_sync(target_org, connector_id):
        captured.append(str(connector_id))
        if connector_id == connector_two.id:
            raise RuntimeError("broker offline")
        return SimpleNamespace(logs=[], task_id="task-123")

    monkeypatch.setattr("app.connectors.admin.services.trigger_sync", fake_trigger_sync)
    client.force_login(admin_user)

    response = client.post(
        reverse("admin:connectors_connectorconfig_changelist"),
        {
            "action": "queue_sync_now",
            ACTION_CHECKBOX_NAME: [str(connector_one.id), str(connector_two.id)],
        },
        follow=True,
    )

    assert response.status_code == 200
    assert set(captured) == {str(connector_one.id), str(connector_two.id)}
    assert b"Queued sync for 1 connector(s)." in response.content
    assert b"Failed to queue sync for 1 connector(s): Connector Two: broker offline" in response.content


def test_connector_admin_dispatch_due_syncs_button_queues_scheduler_run(
    client,
    admin_user,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.connectors.admin.services.dispatch_due_syncs",
        lambda: {
            "queued": 2,
            "skipped": 1,
            "task_ids": ["task-1", "task-2"],
            "errors": [],
        },
    )
    client.force_login(admin_user)

    response = client.post(
        reverse("admin:connectors_connectorconfig_dispatch_due_syncs"),
        follow=True,
    )

    assert response.status_code == 200
    assert b"Dispatch due syncs completed: queued 2, skipped 1, errors 0." in response.content


def test_sync_log_admin_allows_status_change_but_blocks_add_delete(client, admin_user, connector):
    sync_log = SyncLog.objects.create(
        connector=connector,
        org=connector.org,
        entity_type=SyncEntityType.SKU,
        status=SyncStatus.PENDING,
        error_details=[{"error": "upstream timeout"}],
        cursor_state={"page": 2},
    )
    client.force_login(admin_user)

    changelist_response = client.get(reverse("admin:connectors_synclog_changelist"))
    change_response = client.get(reverse("admin:connectors_synclog_change", args=[sync_log.id]))
    add_response = client.get(reverse("admin:connectors_synclog_add"))
    update_response = client.post(
        reverse("admin:connectors_synclog_change", args=[sync_log.id]),
        {"status": SyncStatus.RUNNING, "_save": "Save"},
    )
    delete_response = client.post(reverse("admin:connectors_synclog_delete", args=[sync_log.id]))
    sync_log.refresh_from_db()

    assert changelist_response.status_code == 200
    assert change_response.status_code == 200
    assert b"upstream timeout" in change_response.content
    assert b"&quot;page&quot;: 2" in change_response.content
    assert b'name="status"' in change_response.content
    assert add_response.status_code == 403
    assert update_response.status_code == 302
    assert delete_response.status_code == 403
    assert sync_log.status == SyncStatus.RUNNING
    assert sync_log.started_at is not None
    assert sync_log.completed_at is None


def test_external_entity_mapping_admin_is_read_only(client, admin_user, connector):
    mapping = ExternalEntityMapping.objects.create(
        org=connector.org,
        connector=connector,
        entity_type=SyncEntityType.SKU,
        external_id="EXT-001",
        internal_id=uuid.uuid4(),
        external_hash="abc123",
    )
    client.force_login(admin_user)

    changelist_response = client.get(reverse("admin:connectors_externalentitymapping_changelist"))
    change_response = client.get(
        reverse("admin:connectors_externalentitymapping_change", args=[mapping.id])
    )
    add_response = client.get(reverse("admin:connectors_externalentitymapping_add"))
    update_response = client.post(
        reverse("admin:connectors_externalentitymapping_change", args=[mapping.id]),
        {"external_id": "EXT-UPDATED"},
    )
    delete_response = client.post(
        reverse("admin:connectors_externalentitymapping_delete", args=[mapping.id])
    )

    assert changelist_response.status_code == 200
    assert change_response.status_code == 200
    assert b"EXT-001" in change_response.content
    assert add_response.status_code == 403
    assert update_response.status_code == 403
    assert delete_response.status_code == 403


def test_static_root_is_configured_for_admin_assets():
    assert settings.STATIC_ROOT
