import pytest

from app.core.enums import EntityType, TaskStatus, TransactionType
from app.operations.models import Drop, Pick, Transaction


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


def test_available_tasks_hides_paired_drop_until_pick_completed(
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
        transaction_type=TransactionType.MOVE,
        reference_number="MOVE-001",
    )
    pick = Pick.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        source_entity_type=EntityType.LOCATION,
        source_entity_code="LOC-001",
        quantity="2.0000",
        task_status=TaskStatus.PENDING,
    )
    Drop.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        dest_entity_type=EntityType.LOCATION,
        dest_entity_code="LOC-002",
        quantity="2.0000",
        task_status=TaskStatus.PENDING,
        paired_pick=pick,
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

    assert len(body["data"]["picks"]) == 1
    assert body["data"]["picks"][0]["id"] == str(pick.pk)
    assert body["data"]["drops"] == []


def test_claim_drop_task_requires_linked_pick_completion(
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
        transaction_type=TransactionType.MOVE,
        reference_number="MOVE-002",
    )
    pick = Pick.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        source_entity_type=EntityType.LOCATION,
        source_entity_code="LOC-001",
        quantity="2.0000",
        task_status=TaskStatus.PENDING,
    )
    drop = Drop.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        dest_entity_type=EntityType.LOCATION,
        dest_entity_code="LOC-002",
        quantity="2.0000",
        task_status=TaskStatus.PENDING,
        paired_pick=pick,
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

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["message"] == "Complete the linked pick before claiming this drop."

    drop.refresh_from_db()
    assert drop.task_status == TaskStatus.PENDING
    assert drop.assigned_to_id is None


def test_start_drop_task_requires_linked_pick_completion(
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
        transaction_type=TransactionType.MOVE,
        reference_number="MOVE-003",
    )
    pick = Pick.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        source_entity_type=EntityType.LOCATION,
        source_entity_code="LOC-001",
        quantity="2.0000",
        task_status=TaskStatus.ASSIGNED,
        assigned_to=user,
    )
    drop = Drop.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        dest_entity_type=EntityType.LOCATION,
        dest_entity_code="LOC-002",
        quantity="2.0000",
        task_status=TaskStatus.ASSIGNED,
        assigned_to=user,
        paired_pick=pick,
    )

    response = client.post(
        f"/api/v1/mobile/tasks/drops/{drop.pk}/start",
        content_type="application/json",
        **api_headers(
            org_id=org.id,
            facility_id=facility.code,
            api_key=None,
            authorization="Bearer firebase-token",
        ),
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["message"] == "Complete the linked pick before starting this drop."

    drop.refresh_from_db()
    assert drop.task_status == TaskStatus.ASSIGNED


def test_claim_drop_task_allows_completed_linked_pick(
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
        transaction_type=TransactionType.MOVE,
        reference_number="MOVE-004",
    )
    pick = Pick.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        source_entity_type=EntityType.LOCATION,
        source_entity_code="LOC-001",
        quantity="2.0000",
        task_status=TaskStatus.COMPLETED,
    )
    drop = Drop.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        dest_entity_type=EntityType.LOCATION,
        dest_entity_code="LOC-002",
        quantity="2.0000",
        task_status=TaskStatus.PENDING,
        paired_pick=pick,
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


def test_complete_drop_task_requires_linked_pick_completion(
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
        transaction_type=TransactionType.MOVE,
        reference_number="MOVE-005",
    )
    pick = Pick.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        source_entity_type=EntityType.LOCATION,
        source_entity_code="LOC-001",
        quantity="2.0000",
        task_status=TaskStatus.IN_PROGRESS,
        assigned_to=user,
    )
    drop = Drop.objects.create(
        org=org,
        transaction=txn,
        sku=sku,
        dest_entity_type=EntityType.LOCATION,
        dest_entity_code="LOC-002",
        quantity="2.0000",
        task_status=TaskStatus.IN_PROGRESS,
        assigned_to=user,
        paired_pick=pick,
    )

    response = client.post(
        f"/api/v1/mobile/tasks/drops/{drop.pk}/complete",
        content_type="application/json",
        **api_headers(
            org_id=org.id,
            facility_id=facility.code,
            api_key=None,
            authorization="Bearer firebase-token",
        ),
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["message"] == "Complete the linked pick before completing this drop."

    drop.refresh_from_db()
    assert drop.task_status == TaskStatus.IN_PROGRESS
