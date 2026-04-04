import pytest

from app.ai.models import Conversation


pytestmark = pytest.mark.django_db


def test_create_conversation_preserves_selected_model(
    client,
    allow_firebase,
    api_headers,
    org,
    facility,
    create_app_user,
    grant_org_access,
):
    user = create_app_user(firebase_uid="worker-1", email="worker@example.com")
    grant_org_access(user, org, role_code="viewer")
    allow_firebase(uid="worker-1", email="worker@example.com", name="Worker User")

    response = client.post(
        "/api/v1/ai/conversations",
        data={
            "model_provider": "ollama",
            "model_name": "llama3.2:3b",
        },
        content_type="application/json",
        **api_headers(api_key=None, authorization="Bearer worker-token", org_id=org.id, facility_id=None),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["model_provider"] == "ollama"
    assert body["data"]["model_name"] == "llama3.2:3b"
    assert Conversation.objects.get(id=body["data"]["id"]).model_name == "llama3.2:3b"


def test_update_conversation_model_updates_persisted_selection(
    client,
    allow_firebase,
    api_headers,
    org,
    facility,
    create_app_user,
    grant_org_access,
):
    user = create_app_user(firebase_uid="worker-2", email="worker2@example.com")
    grant_org_access(user, org, role_code="viewer")
    allow_firebase(uid="worker-2", email="worker2@example.com", name="Worker User 2")

    conversation = Conversation.objects.create(
        org=org,
        user=user,
        facility=facility,
        model_provider="ollama",
        model_name="llama3.1",
    )

    response = client.patch(
        f"/api/v1/ai/conversations/{conversation.id}",
        data={
            "model_provider": "ollama",
            "model_name": "llama3.2:3b",
        },
        content_type="application/json",
        **api_headers(api_key=None, authorization="Bearer worker-2-token", org_id=org.id, facility_id=facility.code),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["model_provider"] == "ollama"
    assert body["data"]["model_name"] == "llama3.2:3b"

    conversation.refresh_from_db()
    assert conversation.model_name == "llama3.2:3b"
