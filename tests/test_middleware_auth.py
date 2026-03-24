import pytest

from app.auth.firebase_verifier import FirebaseInvalidTokenError


class RejectVerifier:
    def verify(self, token: str):
        raise FirebaseInvalidTokenError("Firebase token is invalid.")


pytestmark = pytest.mark.django_db


def test_health_is_public(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True


def test_missing_credentials_rejected(client, api_headers):
    response = client.get("/api/v1/inventory/balances", **api_headers(api_key=None))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_MISSING_CREDENTIAL"


def test_accepts_bearer_firebase_token(client, allow_firebase, api_headers):
    response = client.get("/api/v1/masters/organizations", **api_headers(api_key=None, authorization="Bearer firebase-token", org_id=None, facility_id=None))

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["auth_source"] == "firebase"
    assert body["meta"]["uid"] == "firebase-user-1"


def test_accepts_raw_firebase_token(client, allow_firebase, api_headers):
    response = client.get("/api/v1/masters/organizations", **api_headers(api_key=None, authorization="raw-firebase-token", org_id=None, facility_id=None))

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["auth_source"] == "firebase"


def test_fallback_to_api_key_when_firebase_missing(client, api_headers):
    response = client.get("/api/v1/masters/organizations", **api_headers(org_id=None, facility_id=None))

    assert response.status_code == 200
    assert response.json()["meta"]["auth_source"] == "api_key"


def test_fallback_to_api_key_when_firebase_invalid(client, monkeypatch):
    monkeypatch.setattr("app.auth.middleware.get_firebase_verifier", lambda: RejectVerifier())
    response = client.get(
        "/api/v1/masters/organizations",
        HTTP_WAREHOUSE="TEST_WH9",
        HTTP_AUTHORIZATION="Bearer bad-token",
        HTTP_X_API_KEY="legacy-secret",
    )

    assert response.status_code == 200
    assert response.json()["meta"]["auth_source"] == "api_key"


def test_reject_when_firebase_and_api_key_invalid(client, monkeypatch):
    monkeypatch.setattr("app.auth.middleware.get_firebase_verifier", lambda: RejectVerifier())

    response = client.get(
        "/api/v1/masters/organizations",
        HTTP_WAREHOUSE="TEST_WH9",
        HTTP_AUTHORIZATION="Bearer bad-token",
        HTTP_X_API_KEY="wrong-key",
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_FIREBASE_INVALID_TOKEN"


def test_missing_warehouse_header_rejected(client):
    response = client.get(
        "/api/v1/inventory/balances",
        HTTP_X_ORG_ID="testorg",
        HTTP_X_API_KEY="legacy-secret",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "TENANT_MISSING_WAREHOUSE"


def test_missing_org_header_rejected(client):
    response = client.get("/api/v1/inventory/balances", HTTP_WAREHOUSE="TEST_WH9", HTTP_X_API_KEY="legacy-secret")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "TENANT_RESOLUTION_ERROR"


def test_missing_facility_header_rejected_for_facility_scoped_route(client, org):
    response = client.post(
        "/api/v1/operations/move",
        data={
            "sku_code": "SKU-001",
            "source_entity_code": "LOC-001",
            "dest_entity_code": "LOC-002",
            "quantity": 1,
        },
        content_type="application/json",
        HTTP_WAREHOUSE="TEST_WH9",
        HTTP_X_ORG_ID="testorg",
        HTTP_X_API_KEY="legacy-secret",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "TENANT_RESOLUTION_ERROR"
