from __future__ import annotations

import os

import pytest

from app.auth.firebase_verifier import get_firebase_verifier
from app.core.config import get_runtime_settings
from app.masters.models import (
    AppUser,
    AppUserStatus,
    Facility,
    Location,
    MembershipStatus,
    Organization,
    Role,
    SKU,
    UserMembershipFacility,
    UserOrgMembership,
    UserPlatformRole,
    Zone,
)

os.environ.setdefault("LOG_DESTINATION", "firehose")


class AllowVerifier:
    def __init__(self, claims: dict | None = None):
        self.claims = claims or {}

    def verify(self, token: str):
        payload = {
            "uid": "firebase-user-1",
            "email": "firebase-user-1@example.com",
            "name": "Firebase User 1",
            "token": token,
        }
        payload.update(self.claims)
        return payload


@pytest.fixture(autouse=True)
def default_env(monkeypatch):
    monkeypatch.setenv("AUTH_FALLBACK_ENABLED", "true")
    monkeypatch.setenv("LEGACY_API_KEYS", '{"legacy_client":"legacy-secret"}')
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "demo-project")
    monkeypatch.setenv("BOOTSTRAP_PLATFORM_ADMIN_UIDS", "")
    monkeypatch.setenv("LOG_DESTINATION", "firehose")

    get_runtime_settings.cache_clear()
    get_firebase_verifier.cache_clear()
    yield
    get_runtime_settings.cache_clear()
    get_firebase_verifier.cache_clear()


@pytest.fixture
def allow_firebase(monkeypatch):
    def _allow(**claims):
        monkeypatch.setattr("app.auth.middleware.get_firebase_verifier", lambda: AllowVerifier(claims))

    _allow()
    return _allow


@pytest.fixture
def api_headers():
    def _build(
        *,
        warehouse: str | None = "TEST_WH9",
        org_id: str | None = "testorg",
        facility_id: str | None = "FAC-001",
        api_key: str | None = "legacy-secret",
        authorization: str | None = None,
    ) -> dict[str, str]:
        headers: dict[str, str] = {}
        if warehouse is not None:
            headers["HTTP_WAREHOUSE"] = warehouse
        if org_id is not None:
            headers["HTTP_X_ORG_ID"] = org_id
        if facility_id is not None:
            headers["HTTP_X_FACILITY_ID"] = facility_id
        if api_key is not None:
            headers["HTTP_X_API_KEY"] = api_key
        if authorization is not None:
            headers["HTTP_AUTHORIZATION"] = authorization
        return headers

    return _build


@pytest.fixture
def org(db):
    return Organization.objects.create(id="testorg", name="Test Organization")


@pytest.fixture
def org2(db):
    return Organization.objects.create(id="otherorg", name="Other Organization")


@pytest.fixture
def zone(db, org):
    return Zone.objects.create(org=org, code="ZONE-A", name="Zone A")


@pytest.fixture
def zone2(db, org):
    return Zone.objects.create(org=org, code="ZONE-B", name="Zone B")


@pytest.fixture
def location(db, org, zone):
    return Location.objects.create(
        org=org,
        code="LOC-001",
        name="Location 001",
        zone=zone,
    )


@pytest.fixture
def location2(db, org, zone):
    return Location.objects.create(
        org=org,
        code="LOC-002",
        name="Location 002",
        zone=zone,
    )


@pytest.fixture
def sku(db, org):
    return SKU.objects.create(
        org=org,
        code="SKU-001",
        name="Test SKU",
        unit_of_measure="EA",
    )


@pytest.fixture
def sku2(db, org):
    return SKU.objects.create(
        org=org,
        code="SKU-002",
        name="Test SKU 2",
        unit_of_measure="KG",
    )


@pytest.fixture
def facility(db, org):
    return Facility.objects.create(
        org=org,
        code="FAC-001",
        warehouse_key="TEST_WH9",
        name="Test Facility",
    )


@pytest.fixture
def facility2(db, org):
    return Facility.objects.create(
        org=org,
        code="FAC-002",
        warehouse_key="TEST_WH10",
        name="Test Facility 2",
    )


@pytest.fixture
def create_app_user(db):
    def _create(
        *,
        firebase_uid: str = "firebase-user-1",
        email: str = "firebase-user-1@example.com",
        display_name: str = "Firebase User 1",
        status: str = AppUserStatus.ACTIVE,
    ) -> AppUser:
        return AppUser.objects.create(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            status=status,
        )

    return _create


@pytest.fixture
def grant_org_access(db):
    def _grant(
        user: AppUser,
        org: Organization,
        *,
        role_code: str = "org_admin",
        facility_codes: list[str] | None = None,
        status: str = MembershipStatus.ACTIVE,
    ) -> UserOrgMembership:
        role = Role.objects.get(code=role_code)
        membership = UserOrgMembership.objects.create(
            user=user,
            org=org,
            role=role,
            status=status,
        )
        if facility_codes:
            facilities = Facility.objects.filter(org=org, code__in=facility_codes)
            UserMembershipFacility.objects.bulk_create(
                [
                    UserMembershipFacility(membership=membership, facility=facility)
                    for facility in facilities
                ]
            )
        return membership

    return _grant


@pytest.fixture
def assign_platform_admin(db):
    def _assign(user: AppUser) -> UserPlatformRole:
        role = Role.objects.get(code="platform_admin")
        return UserPlatformRole.objects.create(user=user, role=role)

    return _assign
