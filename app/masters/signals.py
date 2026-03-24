from django.db.models.signals import post_save
from django.dispatch import receiver

from app.masters.models import (
    Facility,
    FacilityLocation,
    FacilitySKU,
    FacilityZone,
    Location,
    SKU,
    Zone,
)


@receiver(post_save, sender=Facility)
def auto_map_facility(sender, instance, created, **kwargs):
    """When a new Facility is created, map all existing org SKUs/Zones/Locations to it."""
    if not created:
        return

    org = instance.org

    sku_mappings = [
        FacilitySKU(facility=instance, sku=sku)
        for sku in SKU.objects.filter(org=org)
    ]
    if sku_mappings:
        FacilitySKU.objects.bulk_create(sku_mappings, ignore_conflicts=True)

    zone_mappings = [
        FacilityZone(facility=instance, zone=zone)
        for zone in Zone.objects.filter(org=org)
    ]
    if zone_mappings:
        FacilityZone.objects.bulk_create(zone_mappings, ignore_conflicts=True)

    location_mappings = [
        FacilityLocation(facility=instance, location=location)
        for location in Location.objects.filter(org=org)
    ]
    if location_mappings:
        FacilityLocation.objects.bulk_create(location_mappings, ignore_conflicts=True)


@receiver(post_save, sender=SKU)
def auto_map_sku(sender, instance, created, **kwargs):
    """When a new SKU is created, map it to all existing org Facilities."""
    if not created:
        return

    mappings = [
        FacilitySKU(facility=facility, sku=instance)
        for facility in Facility.objects.filter(org=instance.org)
    ]
    if mappings:
        FacilitySKU.objects.bulk_create(mappings, ignore_conflicts=True)


@receiver(post_save, sender=Zone)
def auto_map_zone(sender, instance, created, **kwargs):
    """When a new Zone is created, map it to all existing org Facilities."""
    if not created:
        return

    mappings = [
        FacilityZone(facility=facility, zone=instance)
        for facility in Facility.objects.filter(org=instance.org)
    ]
    if mappings:
        FacilityZone.objects.bulk_create(mappings, ignore_conflicts=True)


@receiver(post_save, sender=Location)
def auto_map_location(sender, instance, created, **kwargs):
    """When a new Location is created, map it to all existing org Facilities."""
    if not created:
        return

    mappings = [
        FacilityLocation(facility=facility, location=instance)
        for facility in Facility.objects.filter(org=instance.org)
    ]
    if mappings:
        FacilityLocation.objects.bulk_create(mappings, ignore_conflicts=True)
