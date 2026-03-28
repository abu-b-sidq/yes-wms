from django.db import models
from django.db.models import Q

from app.core.base_models import TenantAwareModel, TimestampedModel, UUIDPrimaryKeyMixin


class AppUserStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"


class RoleScope(models.TextChoices):
    PLATFORM = "PLATFORM", "Platform"
    ORG = "ORG", "Organization"


class MembershipStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class Organization(TimestampedModel):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "app_organization"

    def __str__(self):
        return f"{self.id} - {self.name}"


class AppUser(UUIDPrimaryKeyMixin, TimestampedModel):
    firebase_uid = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True, default="", db_index=True)
    display_name = models.CharField(max_length=255, blank=True, default="")
    phone_number = models.CharField(max_length=32, blank=True, default="")
    photo_url = models.URLField(max_length=500, blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=AppUserStatus.choices,
        default=AppUserStatus.PENDING,
        db_index=True,
    )
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_facility = models.ForeignKey(
        "app_masters.Facility",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="last_active_users",
    )

    class Meta:
        db_table = "app_user"
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=~Q(email=""),
                name="uq_app_user_email_non_empty",
            ),
        ]

    def __str__(self):
        return self.email or self.firebase_uid


class Permission(TimestampedModel):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "app_permission"

    def __str__(self):
        return self.code


class Role(TimestampedModel):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    scope = models.CharField(max_length=16, choices=RoleScope.choices)
    permissions = models.ManyToManyField(
        "app_masters.Permission",
        through="app_masters.RolePermission",
        related_name="roles",
    )

    class Meta:
        db_table = "app_role"

    def __str__(self):
        return self.code


class RolePermission(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="permission_roles",
    )

    class Meta:
        db_table = "app_role_permission"
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="uq_role_permission"),
        ]


class UserPlatformRole(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name="platform_role_assignments",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="platform_assignments",
    )

    class Meta:
        db_table = "app_user_platform_role"
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uq_user_platform_role"),
        ]


class UserOrgMembership(UUIDPrimaryKeyMixin, TimestampedModel):
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name="org_memberships",
    )
    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="user_memberships",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="org_role_memberships",
    )
    status = models.CharField(
        max_length=16,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        db_table = "app_user_org_membership"
        constraints = [
            models.UniqueConstraint(fields=["user", "org"], name="uq_user_org_membership"),
        ]


class UserMembershipFacility(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    membership = models.ForeignKey(
        UserOrgMembership,
        on_delete=models.CASCADE,
        related_name="facility_assignments",
    )
    facility = models.ForeignKey(
        "app_masters.Facility",
        on_delete=models.CASCADE,
        related_name="membership_assignments",
    )

    class Meta:
        db_table = "app_user_membership_facility"
        constraints = [
            models.UniqueConstraint(
                fields=["membership", "facility"],
                name="uq_user_membership_facility",
            ),
        ]


class Facility(TenantAwareModel):
    code = models.CharField(max_length=100)
    warehouse_key = models.CharField(max_length=100)
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
            models.UniqueConstraint(fields=["org", "warehouse_key"], name="uq_facility_org_warehouse_key"),
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
