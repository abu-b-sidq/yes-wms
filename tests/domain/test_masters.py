import pytest
from django.db import IntegrityError

from app.core.exceptions import EntityNotFoundError, ValidationError
from app.masters import services
from app.masters.models import Facility, Location, Organization, SKU, Zone


class TestOrganization:
    def test_create_organization(self, db):
        org = services.create_organization({"id": "myorg", "name": "My Org"})
        assert org.id == "myorg"
        assert org.name == "My Org"
        assert org.is_active is True

    def test_create_duplicate_organization(self, org):
        with pytest.raises(ValidationError, match="already exists"):
            services.create_organization({"id": "testorg", "name": "Duplicate"})

    def test_get_organization(self, org):
        fetched = services.get_organization("testorg")
        assert fetched.id == org.id

    def test_get_organization_not_found(self, db):
        with pytest.raises(EntityNotFoundError):
            services.get_organization("nonexistent")

    def test_update_organization(self, org):
        updated = services.update_organization("testorg", {"name": "Updated Name"})
        assert updated.name == "Updated Name"

    def test_list_organizations(self, org, org2):
        orgs = services.list_organizations()
        assert len(orgs) == 2


class TestFacility:
    def test_create_facility(self, org):
        facility = services.create_facility(
            org, {"code": "FAC-X", "warehouse_key": "WH-FAC-X", "name": "Facility X"}
        )
        assert facility.code == "FAC-X"
        assert facility.warehouse_key == "WH-FAC-X"
        assert facility.org_id == "testorg"

    def test_create_duplicate_facility(self, org, facility):
        with pytest.raises(ValidationError, match="already exists"):
            services.create_facility(
                org,
                {"code": "FAC-001", "warehouse_key": "WH-DUP", "name": "Dup"},
            )

    def test_get_facility(self, org, facility):
        fetched = services.get_facility(org, "FAC-001")
        assert fetched.id == facility.id

    def test_update_facility(self, org, facility):
        updated = services.update_facility(
            org, "FAC-001", {"name": "Updated Facility", "warehouse_key": "TEST_WH9-UPDATED"}
        )
        assert updated.name == "Updated Facility"
        assert updated.warehouse_key == "TEST_WH9-UPDATED"

    def test_list_facilities(self, org, facility, facility2):
        facilities = services.list_facilities(org)
        assert len(facilities) == 2


class TestSKU:
    def test_create_sku(self, org):
        sku = services.create_sku(org, {"code": "SKU-X", "name": "SKU X"})
        assert sku.code == "SKU-X"
        assert sku.unit_of_measure == "EA"

    def test_create_duplicate_sku(self, org, sku):
        with pytest.raises(ValidationError, match="already exists"):
            services.create_sku(org, {"code": "SKU-001", "name": "Dup"})

    def test_get_sku(self, org, sku):
        fetched = services.get_sku(org, "SKU-001")
        assert fetched.id == sku.id

    def test_update_sku(self, org, sku):
        updated = services.update_sku(org, "SKU-001", {"name": "Updated SKU"})
        assert updated.name == "Updated SKU"

    def test_list_skus(self, org, sku, sku2):
        skus = services.list_skus(org)
        assert len(skus) == 2


class TestZone:
    def test_create_zone(self, org):
        zone = services.create_zone(org, {"code": "Z-X", "name": "Zone X"})
        assert zone.code == "Z-X"

    def test_create_duplicate_zone(self, org, zone):
        with pytest.raises(ValidationError, match="already exists"):
            services.create_zone(org, {"code": "ZONE-A", "name": "Dup"})

    def test_get_zone(self, org, zone):
        fetched = services.get_zone(org, "ZONE-A")
        assert fetched.id == zone.id

    def test_list_zones(self, org, zone, zone2):
        zones = services.list_zones(org)
        assert len(zones) == 2


class TestLocation:
    def test_create_location(self, org, zone):
        loc = services.create_location(
            org, {"code": "LOC-X", "name": "Loc X", "zone_code": "ZONE-A"}
        )
        assert loc.code == "LOC-X"
        assert loc.zone_id == zone.id

    def test_create_location_invalid_zone(self, org):
        with pytest.raises(EntityNotFoundError, match="Zone"):
            services.create_location(
                org, {"code": "LOC-X", "name": "Loc X", "zone_code": "INVALID"}
            )

    def test_create_duplicate_location(self, org, zone, location):
        with pytest.raises(ValidationError, match="already exists"):
            services.create_location(
                org, {"code": "LOC-001", "name": "Dup", "zone_code": "ZONE-A"}
            )

    def test_get_location(self, org, location):
        fetched = services.get_location(org, "LOC-001")
        assert fetched.id == location.id

    def test_update_location_change_zone(self, org, zone2, location):
        updated = services.update_location(
            org, "LOC-001", {"zone_code": "ZONE-B"}
        )
        assert updated.zone_id == zone2.id

    def test_list_locations(self, org, location, location2):
        locations = services.list_locations(org)
        assert len(locations) == 2
