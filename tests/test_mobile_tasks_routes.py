import pytest

from app.core.enums import EntityType, TaskStatus, TransactionType
from app.operations.models import Drop, Transaction


pytestmark = pytest.mark.django_db


def test_available_tasks_includes_pending_drop_tasks(
    client,
    allow_firebase,
    api_headers,
    org,
    facility,
    sku,
    create_app_user,
    grant_org_access,
):
    user = create_app_user(firebase_uid="worker-1", email="worker@example.com")
    grant_org_access(user, org, facility_codes=[facility.code])
    allow_firebase(uid="worker-1", email="worker@example.com", name="Worker User")

    txn = Transaction.objects.create(
        org=org,
        facility=facility,
        transaction_type=TransactionType.GRN,
        reference_number="GRN-001",
    )
    drop = Drop.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        dest_entity_type=EntityType.ZONE,
        dest_entity_code="PRE_PUTAWAY",
        quantity="5.0000",
        task_status=TaskStatus.PENDING,
    )

    response = client.get(
        "/api/v1/mobile/tasks/available",
        **api_headers(
            org_id=org.id,
            facility_id=facility.code,
            api_key=None,
            authorization="Bearer firebase-token",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert body["data"]["picks"] == []
    assert len(body["data"]["drops"]) == 1
    assert body["data"]["drops"][0]["id"] == str(drop.pk)
    assert body["data"]["drops"][0]["task_status"] == TaskStatus.PENDING


def test_claim_drop_task_assigns_pending_drop_to_current_worker(
    client,
    allow_firebase,
    api_headers,
    org,
    facility,
    sku,
    create_app_user,
    grant_org_access,
    monkeypatch,
):
    monkeypatch.setattr("app.operations.mobile_routes._notify_task_claimed", lambda *args: None)

    user = create_app_user(
        firebase_uid="worker-1",
        email="worker@example.com",
        display_name="Worker User",
    )
    grant_org_access(user, org, facility_codes=[facility.code])
    allow_firebase(uid="worker-1", email="worker@example.com", name="Worker User")

    txn = Transaction.objects.create(
        org=org,
        facility=facility,
        transaction_type=TransactionType.GRN,
        reference_number="GRN-002",
    )
    drop = Drop.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        dest_entity_type=EntityType.ZONE,
        dest_entity_code="PRE_PUTAWAY",
        quantity="3.0000",
        task_status=TaskStatus.PENDING,
    )

    response = client.post(
        f"/api/v1/mobile/tasks/drops/{drop.pk}/claim",
        content_type="application/json",
        **api_headers(
            org_id=org.id,
            facility_id=facility.code,
            api_key=None,
            authorization="Bearer firebase-token",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == str(drop.pk)
    assert body["data"]["task_status"] == TaskStatus.ASSIGNED
    assert body["data"]["assigned_to_name"] == user.display_name

    drop.refresh_from_db()
    assert drop.assigned_to_id == user.pk
    assert drop.task_status == TaskStatus.ASSIGNED
    assert drop.locked_by_id == user.pk
    assert drop.assigned_at is not None
    assert drop.lock_expires_at is not None
