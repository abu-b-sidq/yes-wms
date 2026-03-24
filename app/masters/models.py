from django.db import models

from app.core.base_models import TenantAwareModel, TimestampedModel


class Organization(TimestampedModel):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "app_organization"

    def __str__(self):
        return f"{self.id} - {self.name}"


class Facility(TenantAwareModel):
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    address = models.TextField(blank=True, default="")

    skus = models.ManyToManyField(
        "app_masters.SKU",
        through="app_masters.FacilitySKU",
        related_name="facilities",
    )
    zones = models.ManyToManyField(
        "app_masters.Zone",
        through="app_masters.FacilityZone",
        related_name="facilities",
    )
    locations = models.ManyToManyField(
        "app_masters.Location",
        through="app_masters.FacilityLocation",
        related_name="facilities",
    )

    class Meta:
        db_table = "app_facility"
        constraints = [
            models.UniqueConstraint(fields=["org", "code"], name="uq_facility_org_code"),
        ]

    def __str__(self):
        return f"{self.org_id}/{self.code}"


class SKU(TenantAwareModel):
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    unit_of_measure = models.CharField(max_length=20, default="EA")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "app_sku"
        constraints = [
            models.UniqueConstraint(fields=["org", "code"], name="uq_sku_org_code"),
        ]

    def __str__(self):
        return f"{self.org_id}/{self.code}"


class Zone(TenantAwareModel):
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "app_zone"
        constraints = [
            models.UniqueConstraint(fields=["org", "code"], name="uq_zone_org_code"),
        ]

    def __str__(self):
        return f"{self.org_id}/{self.code}"


class Location(TenantAwareModel):
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="locations")
    is_active = models.BooleanField(default=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "app_location"
        constraints = [
            models.UniqueConstraint(fields=["org", "code"], name="uq_location_org_code"),
        ]

    def __str__(self):
        return f"{self.org_id}/{self.code}"


class FacilitySKU(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    overrides = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "app_facility_sku"
        constraints = [
            models.UniqueConstraint(fields=["facility", "sku"], name="uq_facility_sku"),
        ]


class FacilityZone(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    overrides = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "app_facility_zone"
        constraints = [
            models.UniqueConstraint(fields=["facility", "zone"], name="uq_facility_zone"),
        ]


class FacilityLocation(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    overrides = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "app_facility_location"
        constraints = [
            models.UniqueConstraint(
                fields=["facility", "location"], name="uq_facility_location"
            ),
        ]
