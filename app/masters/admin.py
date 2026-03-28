from django.contrib import admin

from app.masters.models import (
    AppUser,
    Facility,
    FacilityLocation,
    FacilitySKU,
    FacilityZone,
    Location,
    Organization,
    Permission,
    Role,
    RolePermission,
    SKU,
    UserMembershipFacility,
    UserOrgMembership,
    UserPlatformRole,
    Zone,
)


class TimestampedAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1
    autocomplete_fields = ("permission",)


class UserPlatformRoleInline(admin.TabularInline):
    model = UserPlatformRole
    extra = 0
    autocomplete_fields = ("role",)
    show_change_link = True


class UserMembershipFacilityInline(admin.TabularInline):
    model = UserMembershipFacility
    extra = 0
    autocomplete_fields = ("facility",)


class UserOrgMembershipInline(admin.TabularInline):
    model = UserOrgMembership
    extra = 0
    autocomplete_fields = ("org", "role")
    show_change_link = True


@admin.register(Organization)
class OrganizationAdmin(TimestampedAdmin):
    list_display = ("id", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("id", "name")


@admin.register(AppUser)
class AppUserAdmin(TimestampedAdmin):
    list_display = (
        "email",
        "firebase_uid",
        "display_name",
        "status",
        "last_login_at",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("email", "firebase_uid", "display_name", "phone_number")
    readonly_fields = TimestampedAdmin.readonly_fields + ("last_login_at",)
    inlines = [UserPlatformRoleInline, UserOrgMembershipInline]


@admin.register(Permission)
class PermissionAdmin(TimestampedAdmin):
    list_display = ("code", "name", "created_at")
    search_fields = ("code", "name", "description")


@admin.register(Role)
class RoleAdmin(TimestampedAdmin):
    list_display = ("code", "name", "scope", "created_at")
    list_filter = ("scope",)
    search_fields = ("code", "name", "description")
    inlines = [RolePermissionInline]


@admin.register(RolePermission)
class RolePermissionAdmin(TimestampedAdmin):
    list_display = ("role", "permission", "created_at")
    list_select_related = ("role", "permission")
    autocomplete_fields = ("role", "permission")
    search_fields = ("role__code", "role__name", "permission__code", "permission__name")


@admin.register(UserPlatformRole)
class UserPlatformRoleAdmin(TimestampedAdmin):
    list_display = ("user", "role", "created_at")
    list_select_related = ("user", "role")
    autocomplete_fields = ("user", "role")
    search_fields = ("user__email", "user__firebase_uid", "role__code", "role__name")


@admin.register(UserOrgMembership)
class UserOrgMembershipAdmin(TimestampedAdmin):
    list_display = ("user", "org", "role", "status", "created_at")
    list_filter = ("status", "org", "role")
    list_select_related = ("user", "org", "role")
    autocomplete_fields = ("user", "org", "role")
    search_fields = (
        "user__email",
        "user__firebase_uid",
        "org__id",
        "org__name",
        "role__code",
        "role__name",
    )
    inlines = [UserMembershipFacilityInline]


@admin.register(UserMembershipFacility)
class UserMembershipFacilityAdmin(TimestampedAdmin):
    list_display = ("membership", "facility", "created_at")
    list_select_related = ("membership", "facility", "membership__user", "membership__org")
    autocomplete_fields = ("membership", "facility")
    search_fields = (
        "membership__user__email",
        "membership__user__firebase_uid",
        "membership__org__id",
        "facility__code",
        "facility__name",
    )


@admin.register(Facility)
class FacilityAdmin(TimestampedAdmin):
    list_display = ("code", "name", "org", "is_active", "created_at")
    list_filter = ("org", "is_active")
    list_select_related = ("org",)
    search_fields = ("code", "name", "org__id", "org__name", "address")


@admin.register(SKU)
class SKUAdmin(TimestampedAdmin):
    list_display = ("code", "name", "org", "unit_of_measure", "is_active")
    list_filter = ("org", "is_active", "unit_of_measure")
    list_select_related = ("org",)
    search_fields = ("code", "name", "org__id", "org__name")


@admin.register(Zone)
class ZoneAdmin(TimestampedAdmin):
    list_display = ("code", "name", "org", "is_active")
    list_filter = ("org", "is_active")
    list_select_related = ("org",)
    search_fields = ("code", "name", "org__id", "org__name")


@admin.register(Location)
class LocationAdmin(TimestampedAdmin):
    list_display = ("code", "name", "org", "zone", "is_active")
    list_filter = ("org", "zone", "is_active")
    list_select_related = ("org", "zone")
    search_fields = ("code", "name", "org__id", "org__name", "zone__code", "zone__name")


@admin.register(FacilitySKU)
class FacilitySKUAdmin(TimestampedAdmin):
    list_display = ("facility", "sku", "is_active", "created_at")
    list_filter = ("is_active", "facility__org")
    list_select_related = ("facility", "sku", "facility__org", "sku__org")
    autocomplete_fields = ("facility", "sku")
    search_fields = (
        "facility__code",
        "facility__name",
        "sku__code",
        "sku__name",
        "facility__org__id",
    )


@admin.register(FacilityZone)
class FacilityZoneAdmin(TimestampedAdmin):
    list_display = ("facility", "zone", "is_active", "created_at")
    list_filter = ("is_active", "facility__org")
    list_select_related = ("facility", "zone", "facility__org", "zone__org")
    autocomplete_fields = ("facility", "zone")
    search_fields = (
        "facility__code",
        "facility__name",
        "zone__code",
        "zone__name",
        "facility__org__id",
    )


@admin.register(FacilityLocation)
class FacilityLocationAdmin(TimestampedAdmin):
    list_display = ("facility", "location", "is_active", "created_at")
    list_filter = ("is_active", "facility__org")
    list_select_related = ("facility", "location", "facility__org", "location__zone")
    autocomplete_fields = ("facility", "location")
    search_fields = (
        "facility__code",
        "facility__name",
        "location__code",
        "location__name",
        "facility__org__id",
    )
