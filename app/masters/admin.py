from django.contrib import admin

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


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "created_at")
    search_fields = ("id", "name")


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "org", "is_active", "created_at")
    list_filter = ("org", "is_active")
    search_fields = ("code", "name")


@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "org", "unit_of_measure", "is_active")
    list_filter = ("org", "is_active")
    search_fields = ("code", "name")


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "org", "is_active")
    list_filter = ("org", "is_active")
    search_fields = ("code", "name")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "org", "zone", "is_active")
    list_filter = ("org", "zone", "is_active")
    search_fields = ("code", "name")


@admin.register(FacilitySKU)
class FacilitySKUAdmin(admin.ModelAdmin):
    list_display = ("facility", "sku", "is_active")
    list_filter = ("is_active",)


@admin.register(FacilityZone)
class FacilityZoneAdmin(admin.ModelAdmin):
    list_display = ("facility", "zone", "is_active")
    list_filter = ("is_active",)


@admin.register(FacilityLocation)
class FacilityLocationAdmin(admin.ModelAdmin):
    list_display = ("facility", "location", "is_active")
    list_filter = ("is_active",)
