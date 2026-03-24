from __future__ import annotations

import os

import pytest

from app.auth.firebase_verifier import get_firebase_verifier
from app.core.config import get_runtime_settings
from app.masters.models import Facility, Location, Organization, SKU, Zone

os.environ.setdefault("LOG_DESTINATION", "firehose")


class AllowVerifier:
    def verify(self, token: str):
        return {"uid": "firebase-user-1", "token": token}


@pytest.fixture(autouse=True)
def default_env(monkeypatch):
    monkeypatch.setenv("AUTH_FALLBACK_ENABLED", "true")
    monkeypatch.setenv("LEGACY_API_KEYS", '{"legacy_client":"legacy-secret"}')
    monkeypatch.setenv("WAREHOUSE_CONFIG", '{"TEST_WH9":{"name":"Test Warehouse"}}')
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "demo-project")
    monkeypatch.setenv("LOG_DESTINATION", "firehose")

    get_runtime_settings.cache_clear()
    get_firebase_verifier.cache_clear()
    yield
    get_runtime_settings.cache_clear()
    get_firebase_verifier.cache_clear()


@pytest.fixture
def allow_firebase(monkeypatch):
    monkeypatch.setattr("app.auth.middleware.get_firebase_verifier", lambda: AllowVerifier())


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
        name="Test Facility",
    )


@pytest.fixture
def facility2(db, org):
    return Facility.objects.create(
        org=org,
        code="FAC-002",
        name="Test Facility 2",
    )
