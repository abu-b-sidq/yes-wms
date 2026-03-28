import pytest

from app.masters.models import AppUser, AppUserStatus


pytestmark = pytest.mark.django_db


def test_org_admin_can_grant_access_after_user_logs_in_once(
    client,
    allow_firebase,
    api_headers,
    org,
    facility,
    create_app_user,
    grant_org_access,
):
    admin_user = create_app_user(firebase_uid="admin-1", email="admin@example.com")
    grant_org_access(admin_user, org, role_code="org_admin")

    allow_firebase(uid="worker-1", email="worker@example.com", name="Worker User")
    me_response = client.get(
        "/api/v1/masters/me",
        **api_headers(api_key=None, authorization="Bearer worker-token", org_id=None, facility_id=None),
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["status"] == "PENDING"

    allow_firebase(uid="admin-1", email="admin@example.com", name="Admin User")
    grant_response = client.post(
        "/api/v1/masters/users/grants",
        data={
            "email": "worker@example.com",
            "role_code": "viewer",
            "facility_codes": [facility.code],
        },
        content_type="application/json",
        **api_headers(api_key=None, authorization="Bearer admin-token", org_id=org.id, facility_id=None),
    )

    assert grant_response.status_code == 200
    body = grant_response.json()
    assert body["data"]["role_code"] == "viewer"
    assert body["data"]["facility_codes"] == [facility.code]
    assert AppUser.objects.get(email="worker@example.com").status == AppUserStatus.ACTIVE


def test_regular_firebase_user_only_sees_their_orgs(
    client,
    allow_firebase,
    api_headers,
    org,
    org2,
    create_app_user,
    grant_org_access,
):
    app_user = create_app_user(firebase_uid="viewer-1", email="viewer@example.com")
    grant_org_access(app_user, org, role_code="viewer")

    allow_firebase(uid="viewer-1", email="viewer@example.com", name="Viewer User")
    response = client.get(
        "/api/v1/masters/organizations",
        **api_headers(api_key=None, authorization="Bearer viewer-token", org_id=None, facility_id=None),
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [org.id]


def test_facility_restricted_user_must_send_facility_header_on_optional_facility_routes(
    client,
    allow_firebase,
    api_headers,
    org,
    facility,
    create_app_user,
    grant_org_access,
):
    app_user = create_app_user(firebase_uid="restricted-1", email="restricted@example.com")
    grant_org_access(app_user, org, role_code="viewer", facility_codes=[facility.code])

    allow_firebase(uid="restricted-1", email="restricted@example.com", name="Restricted User")
    response = client.get(
        "/api/v1/inventory/balances",
        **api_headers(api_key=None, authorization="Bearer restricted-token", org_id=org.id, facility_id=None),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTHZ_FACILITY_SCOPE_REQUIRED"


def test_platform_admin_can_list_pending_users_and_update_status(
    client,
    allow_firebase,
    api_headers,
    create_app_user,
    assign_platform_admin,
):
    platform_admin = create_app_user(firebase_uid="platform-1", email="platform@example.com")
    assign_platform_admin(platform_admin)
    pending_user = create_app_user(
        firebase_uid="pending-1",
        email="pending@example.com",
        status=AppUserStatus.PENDING,
    )

    allow_firebase(uid="platform-1", email="platform@example.com", name="Platform Admin")
    pending_response = client.get(
        "/api/v1/masters/users/pending",
        **api_headers(api_key=None, authorization="Bearer platform-token", org_id=None, facility_id=None),
    )

    assert pending_response.status_code == 200
    assert [item["email"] for item in pending_response.json()["data"]] == [pending_user.email]

    status_response = client.patch(
        f"/api/v1/masters/users/{pending_user.id}/status",
        data={"status": "ACTIVE"},
        content_type="application/json",
        **api_headers(api_key=None, authorization="Bearer platform-token", org_id=None, facility_id=None),
    )

    assert status_response.status_code == 200
    pending_user.refresh_from_db()
    assert pending_user.status == AppUserStatus.ACTIVE
