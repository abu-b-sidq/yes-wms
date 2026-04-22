import json
import threading

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


@receiver(post_save, sender=SKU)
def embed_sku(sender, instance, **kwargs):
    """Asynchronously embed SKU for semantic search."""
    metadata_str = json.dumps(instance.metadata) if instance.metadata else ""
    text = f"SKU: {instance.code} | Name: {instance.name} | UOM: {instance.unit_of_measure} | {metadata_str}".strip(" |")

    def _run():
        from app.ai.embeddings import upsert_embedding_sync
        upsert_embedding_sync("sku", str(instance.id), str(instance.org_id), text)

    threading.Thread(target=_run, daemon=True).start()


@receiver(post_save, sender=SKU)
def create_sku_graph_node(sender, instance, **kwargs):
    """Asynchronously create SKU node in knowledge graph."""
    def _run():
        from app.ai.graph_service import GraphService
        service = GraphService.get_instance()
        service.create_sku_node(
            org_id=str(instance.org_id),
            sku_code=instance.code,
            sku_name=instance.name,
            unit_of_measure=instance.unit_of_measure,
            metadata=instance.metadata,
        )

    threading.Thread(target=_run, daemon=True).start()


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


@receiver(post_save, sender=Facility)
def create_facility_graph_node(sender, instance, **kwargs):
    """Asynchronously create Facility node in knowledge graph."""
    def _run():
        from app.ai.graph_service import GraphService
        service = GraphService.get_instance()
        service.create_facility_node(
            org_id=str(instance.org_id),
            facility_code=instance.code,
            facility_name=instance.name,
            warehouse_key=instance.warehouse_key,
            address=instance.address,
        )

    threading.Thread(target=_run, daemon=True).start()


@receiver(post_save, sender=Location)
def create_location_graph_node(sender, instance, **kwargs):
    """Asynchronously create Location node in knowledge graph."""
    def _run():
        from app.ai.graph_service import GraphService
        service = GraphService.get_instance()
        service.create_location_node(
            org_id=str(instance.org_id),
            location_code=instance.code,
            location_name=instance.name,
            zone_code=instance.zone.code if instance.zone else "",
            capacity=instance.capacity,
        )

    threading.Thread(target=_run, daemon=True).start()
