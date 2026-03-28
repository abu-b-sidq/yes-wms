import pytest

from app.masters.models import Facility, Location, Organization, SKU, Zone


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
        org=org, code="LOC-001", name="Location 001", zone=zone
    )


@pytest.fixture
def location2(db, org, zone):
    return Location.objects.create(
        org=org, code="LOC-002", name="Location 002", zone=zone
    )


@pytest.fixture
def sku(db, org):
    return SKU.objects.create(
        org=org, code="SKU-001", name="Test SKU", unit_of_measure="EA"
    )


@pytest.fixture
def sku2(db, org):
    return SKU.objects.create(
        org=org, code="SKU-002", name="Test SKU 2", unit_of_measure="KG"
    )


@pytest.fixture
def facility(db, org):
    return Facility.objects.create(
        org=org, code="FAC-001", warehouse_key="TEST_WH9", name="Test Facility"
    )


@pytest.fixture
def facility2(db, org):
    return Facility.objects.create(
        org=org, code="FAC-002", warehouse_key="TEST_WH10", name="Test Facility 2"
    )
