import pytest

from app.masters.models import (
    Facility,
    FacilityLocation,
    FacilitySKU,
    FacilityZone,
    Location,
    Organization,
    SKU,
    Zone,
)


class TestAutoMapping:
    def test_new_facility_maps_existing_skus(self, org, sku, sku2):
        """Creating a facility should auto-map all existing org SKUs."""
        facility = Facility.objects.create(
            org=org,
            code="FAC-NEW",
            warehouse_key="WH-FAC-NEW",
            name="New Facility",
        )
        mappings = FacilitySKU.objects.filter(facility=facility)
        assert mappings.count() == 2
        sku_codes = set(mappings.values_list("sku__code", flat=True))
        assert sku_codes == {"SKU-001", "SKU-002"}

    def test_new_facility_maps_existing_zones(self, org, zone, zone2):
        """Creating a facility should auto-map all existing org Zones."""
        facility = Facility.objects.create(
            org=org,
            code="FAC-NEW",
            warehouse_key="WH-FAC-NEW",
            name="New Facility",
        )
        mappings = FacilityZone.objects.filter(facility=facility)
        assert mappings.count() == 2

    def test_new_facility_maps_existing_locations(self, org, zone, location, location2):
        """Creating a facility should auto-map all existing org Locations."""
        facility = Facility.objects.create(
            org=org,
            code="FAC-NEW",
            warehouse_key="WH-FAC-NEW",
            name="New Facility",
        )
        mappings = FacilityLocation.objects.filter(facility=facility)
        assert mappings.count() == 2

    def test_new_sku_maps_to_existing_facilities(self, org, facility, facility2):
        """Creating a SKU should auto-map it to all existing org Facilities."""
        sku = SKU.objects.create(org=org, code="SKU-NEW", name="New SKU")
        mappings = FacilitySKU.objects.filter(sku=sku)
        assert mappings.count() == 2
        fac_codes = set(mappings.values_list("facility__code", flat=True))
        assert fac_codes == {"FAC-001", "FAC-002"}

    def test_new_zone_maps_to_existing_facilities(self, org, facility, facility2):
        """Creating a Zone should auto-map it to all existing org Facilities."""
        zone = Zone.objects.create(org=org, code="Z-NEW", name="New Zone")
        mappings = FacilityZone.objects.filter(zone=zone)
        assert mappings.count() == 2

    def test_new_location_maps_to_existing_facilities(self, org, zone, facility, facility2):
        """Creating a Location should auto-map it to all existing org Facilities."""
        loc = Location.objects.create(
            org=org, code="LOC-NEW", name="New Location", zone=zone
        )
        mappings = FacilityLocation.objects.filter(location=loc)
        assert mappings.count() == 2

    def test_auto_mapping_is_idempotent(self, org, sku, facility):
        """Duplicate signal fires should not create duplicate mappings."""
        count_before = FacilitySKU.objects.filter(facility=facility, sku=sku).count()
        # Manually call signal handler again
        from app.masters.signals import auto_map_sku
        auto_map_sku(sender=SKU, instance=sku, created=True)
        count_after = FacilitySKU.objects.filter(facility=facility, sku=sku).count()
        assert count_before == count_after

    def test_no_cross_org_mapping(self, org, org2, facility):
        """SKUs from a different org should NOT be mapped to the facility."""
        other_sku = SKU.objects.create(org=org2, code="OTHER-SKU", name="Other")
        mapping = FacilitySKU.objects.filter(facility=facility, sku=other_sku)
        assert mapping.count() == 0
