from __future__ import annotations

from datetime import datetime

from ninja import Schema


# --- Organization ---

class OrganizationCreateIn(Schema):
    id: str
    name: str


class OrganizationUpdateIn(Schema):
    name: str | None = None
    is_active: bool | None = None


class OrganizationOut(Schema):
    id: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Facility ---

class FacilityCreateIn(Schema):
    code: str
    warehouse_key: str
    name: str
    address: str = ""


class FacilityUpdateIn(Schema):
    warehouse_key: str | None = None
    name: str | None = None
    address: str | None = None
    is_active: bool | None = None


class FacilityOut(Schema):
    id: str
    code: str
    warehouse_key: str
    name: str
    is_active: bool
    address: str
    created_at: datetime
    updated_at: datetime


# --- SKU ---

class SKUCreateIn(Schema):
    code: str
    name: str
    unit_of_measure: str = "EA"
    metadata: dict = {}


class SKUUpdateIn(Schema):
    name: str | None = None
    unit_of_measure: str | None = None
    is_active: bool | None = None
    metadata: dict | None = None


class SKUOut(Schema):
    id: str
    code: str
    name: str
    unit_of_measure: str
    is_active: bool
    metadata: dict
    created_at: datetime
    updated_at: datetime


# --- Zone ---

class ZoneCreateIn(Schema):
    code: str
    name: str


class ZoneUpdateIn(Schema):
    name: str | None = None
    is_active: bool | None = None


class ZoneOut(Schema):
    id: str
    code: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Location ---

class LocationCreateIn(Schema):
    code: str
    name: str
    zone_code: str
    capacity: int | None = None


class LocationUpdateIn(Schema):
    name: str | None = None
    zone_code: str | None = None
    is_active: bool | None = None
    capacity: int | None = None


class LocationOut(Schema):
    id: str
    code: str
    name: str
    zone_code: str
    is_active: bool
    capacity: int | None
    created_at: datetime
    updated_at: datetime


# --- Facility Mapping Overrides ---

class FacilityMappingOverrideIn(Schema):
    is_active: bool | None = None
    overrides: dict | None = None


class FacilitySKUOut(Schema):
    sku_code: str
    sku_name: str
    is_active: bool
    overrides: dict


class FacilityZoneOut(Schema):
    zone_code: str
    zone_name: str
    is_active: bool
    overrides: dict


class FacilityLocationOut(Schema):
    location_code: str
    location_name: str
    is_active: bool
    overrides: dict


class UserGrantCreateIn(Schema):
    email: str
    role_code: str
    facility_codes: list[str] = []


class UserGrantUpdateIn(Schema):
    role_code: str | None = None
    status: str | None = None
    facility_codes: list[str] | None = None


class UserStatusUpdateIn(Schema):
    status: str


class UserPlatformRoleUpdateIn(Schema):
    enabled: bool


class UserMembershipOut(Schema):
    id: str
    org_id: str
    role_code: str
    role_name: str
    status: str
    facility_codes: list[str]
    created_at: datetime
    updated_at: datetime


class OrgUserOut(Schema):
    id: str
    firebase_uid: str
    email: str
    display_name: str
    phone_number: str
    photo_url: str
    status: str
    platform_roles: list[str]
    grant: UserMembershipOut
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PendingUserOut(Schema):
    id: str
    firebase_uid: str
    email: str
    display_name: str
    phone_number: str
    photo_url: str
    status: str
    platform_roles: list[str]
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CurrentUserOut(Schema):
    id: str
    firebase_uid: str
    email: str
    display_name: str
    phone_number: str
    photo_url: str
    status: str
    platform_roles: list[str]
    memberships: list[UserMembershipOut]
    effective_permissions: list[str]
    requested_org_id: str | None
    requested_facility_id: str | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
