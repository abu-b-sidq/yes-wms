from __future__ import annotations

from ninja import Router

from app.auth.authorization import authorize_request, enforce_facility_scope
from app.auth.permissions import (
    PERM_MASTERS_MANAGE,
    PERM_MASTERS_READ,
    PERM_ORG_CREATE,
    PERM_ORG_LIST_ALL,
    PERM_ORG_READ,
    PERM_ORG_UPDATE,
    PERM_USERS_MANAGE_ORG,
    PERM_USERS_MANAGE_PLATFORM,
)
from app.core.openapi import (
    firebase_only_openapi_extra,
    protected_openapi_extra,
    register_response_schema,
)
from app.core.response import success_response
from app.core.tenant import resolve_request_tenant
from app.masters import schemas, services, user_services

router = Router(tags=["masters"])

# ---------------------------------------------------------------------------
# Response data schemas
# ---------------------------------------------------------------------------

_ORG_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "is_active": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
}

_FACILITY_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "code": {"type": "string"},
        "warehouse_key": {"type": "string"},
        "name": {"type": "string"},
        "is_active": {"type": "boolean"},
        "address": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
}

_SKU_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "code": {"type": "string"},
        "name": {"type": "string"},
        "unit_of_measure": {"type": "string"},
        "is_active": {"type": "boolean"},
        "metadata": {"type": "object"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
}

_ZONE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "code": {"type": "string"},
        "name": {"type": "string"},
        "is_active": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
}

_LOCATION_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "code": {"type": "string"},
        "name": {"type": "string"},
        "zone_code": {"type": "string"},
        "is_active": {"type": "boolean"},
        "capacity": {"type": "integer", "nullable": True},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
}

_FAC_SKU_SCHEMA = {
    "type": "object",
    "properties": {
        "sku_code": {"type": "string"},
        "sku_name": {"type": "string"},
        "is_active": {"type": "boolean"},
        "overrides": {"type": "object"},
    },
}
_FAC_ZONE_SCHEMA = {
    "type": "object",
    "properties": {
        "zone_code": {"type": "string"},
        "zone_name": {"type": "string"},
        "is_active": {"type": "boolean"},
        "overrides": {"type": "object"},
    },
}
_FAC_LOCATION_SCHEMA = {
    "type": "object",
    "properties": {
        "location_code": {"type": "string"},
        "location_name": {"type": "string"},
        "is_active": {"type": "boolean"},
        "overrides": {"type": "object"},
    },
}

_USER_GRANT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "org_id": {"type": "string"},
        "role_code": {"type": "string"},
        "role_name": {"type": "string"},
        "status": {"type": "string"},
        "facility_codes": {"type": "array", "items": {"type": "string"}},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
}

_ORG_USER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "firebase_uid": {"type": "string"},
        "email": {"type": "string"},
        "display_name": {"type": "string"},
        "phone_number": {"type": "string"},
        "photo_url": {"type": "string", "format": "uri"},
        "status": {"type": "string"},
        "platform_roles": {"type": "array", "items": {"type": "string"}},
        "grant": _USER_GRANT_SCHEMA,
        "last_login_at": {"type": "string", "format": "date-time", "nullable": True},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
}

_PENDING_USER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "firebase_uid": {"type": "string"},
        "email": {"type": "string"},
        "display_name": {"type": "string"},
        "phone_number": {"type": "string"},
        "photo_url": {"type": "string", "format": "uri"},
        "status": {"type": "string"},
        "platform_roles": {"type": "array", "items": {"type": "string"}},
        "last_login_at": {"type": "string", "format": "date-time", "nullable": True},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
}

_CURRENT_USER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "firebase_uid": {"type": "string"},
        "email": {"type": "string"},
        "display_name": {"type": "string"},
        "phone_number": {"type": "string"},
        "photo_url": {"type": "string", "format": "uri"},
        "status": {"type": "string"},
        "platform_roles": {"type": "array", "items": {"type": "string"}},
        "memberships": {"type": "array", "items": _USER_GRANT_SCHEMA},
        "effective_permissions": {"type": "array", "items": {"type": "string"}},
        "requested_org_id": {"type": "string", "nullable": True},
        "requested_facility_id": {"type": "string", "nullable": True},
        "last_login_at": {"type": "string", "format": "date-time", "nullable": True},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
}


def _list_of(schema: dict) -> dict:
    return {"type": "array", "items": schema}


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------

@router.post(
    "/organizations",
    summary="Create organization",
    description="Create a new top-level organisation. The `id` is chosen by the caller and must be unique.",
    openapi_extra=protected_openapi_extra(require_org=False),
)
def create_organization(request, payload: schemas.OrganizationCreateIn):
    authorize_request(request, PERM_ORG_CREATE)
    org = services.create_organization(payload.dict())
    return success_response(request, data=schemas.OrganizationOut.from_orm(org).dict())


@router.get(
    "/organizations",
    summary="List organizations",
    description="Return all organisations visible to the authenticated warehouse.",
    openapi_extra=protected_openapi_extra(require_org=False),
)
def list_organizations(request):
    access = authorize_request(request)
    if access.is_api_key_bypass or PERM_ORG_LIST_ALL in access.permission_codes:
        orgs = services.list_organizations()
    else:
        orgs = user_services.list_user_organizations(access.app_user)
    return success_response(
        request,
        data=[schemas.OrganizationOut.from_orm(o).dict() for o in orgs],
    )


@router.get(
    "/organizations/{org_id}",
    summary="Get organization",
    description="Retrieve a single organisation by its ID.",
    openapi_extra=protected_openapi_extra(require_org=False),
)
def get_organization(request, org_id: str):
    authorize_request(
        request,
        PERM_ORG_READ,
        org_id=org_id,
        require_membership=True,
    )
    org = services.get_organization(org_id)
    return success_response(request, data=schemas.OrganizationOut.from_orm(org).dict())


@router.patch(
    "/organizations/{org_id}",
    summary="Update organization",
    description="Partially update an organisation's name or active status.",
    openapi_extra=protected_openapi_extra(require_org=False),
)
def update_organization(request, org_id: str, payload: schemas.OrganizationUpdateIn):
    authorize_request(
        request,
        PERM_ORG_UPDATE,
        org_id=org_id,
        require_membership=True,
    )
    org = services.update_organization(org_id, payload.dict(exclude_unset=True))
    return success_response(request, data=schemas.OrganizationOut.from_orm(org).dict())


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    summary="Current user",
    description=(
        "Return the current Firebase-backed user profile, memberships, platform roles, "
        "and effective permissions for the requested org/facility scope when headers are provided."
    ),
    openapi_extra=firebase_only_openapi_extra(include_org=True, include_facility=True),
)
def get_current_user(request):
    access = authorize_request(
        request,
        require_firebase=True,
        allow_pending=True,
        allow_suspended=True,
    )
    return success_response(request, data=_current_user_out(request, access))


@router.get(
    "/users",
    summary="List users in organization",
    description="Return all user access grants in the current organization.",
    openapi_extra=firebase_only_openapi_extra(require_org=True),
)
def list_users(request):
    access = authorize_request(
        request,
        PERM_USERS_MANAGE_ORG,
        require_firebase=True,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    memberships = user_services.list_org_users(org)
    return success_response(
        request,
        data=[_org_user_out(membership) for membership in memberships],
    )


@router.post(
    "/users/grants",
    summary="Grant organization access",
    description=(
        "Grant an organization role to a Firebase-backed user who has already logged in once. "
        "Pass facility codes to restrict access to specific facilities; omit them for org-wide access."
    ),
    openapi_extra=firebase_only_openapi_extra(require_org=True),
)
def create_user_grant(request, payload: schemas.UserGrantCreateIn):
    authorize_request(
        request,
        PERM_USERS_MANAGE_ORG,
        require_firebase=True,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    membership = user_services.grant_org_access(
        org,
        email=payload.email,
        role_code=payload.role_code,
        facility_codes=payload.facility_codes,
    )
    return success_response(request, data=_user_grant_out(membership))


@router.patch(
    "/users/{user_id}/grants/{grant_id}",
    summary="Update organization access grant",
    description="Update the role, membership status, or facility restrictions for a user's org access grant.",
    openapi_extra=firebase_only_openapi_extra(require_org=True),
)
def update_user_grant(
    request,
    user_id: str,
    grant_id: str,
    payload: schemas.UserGrantUpdateIn,
):
    authorize_request(
        request,
        PERM_USERS_MANAGE_ORG,
        require_firebase=True,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    membership = user_services.update_org_access(
        org,
        user_id=user_id,
        grant_id=grant_id,
        role_code=payload.role_code,
        status=payload.status,
        facility_codes=payload.facility_codes,
    )
    return success_response(request, data=_user_grant_out(membership))


@router.delete(
    "/users/{user_id}/grants/{grant_id}",
    summary="Revoke organization access grant",
    description="Delete a user's organization access grant.",
    openapi_extra=firebase_only_openapi_extra(require_org=True),
)
def delete_user_grant(request, user_id: str, grant_id: str):
    authorize_request(
        request,
        PERM_USERS_MANAGE_ORG,
        require_firebase=True,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    user_services.delete_org_access(org, user_id=user_id, grant_id=grant_id)
    return success_response(request, data={"deleted": True})


@router.get(
    "/users/pending",
    summary="List pending users",
    description="Return users who have logged in with Firebase but have not been granted org access yet.",
    openapi_extra=firebase_only_openapi_extra(),
)
def list_pending_users(request):
    authorize_request(
        request,
        PERM_USERS_MANAGE_PLATFORM,
        require_firebase=True,
    )
    users = user_services.list_pending_users()
    return success_response(request, data=[_pending_user_out(user) for user in users])


@router.patch(
    "/users/{user_id}/status",
    summary="Update user status",
    description="Set a Firebase-backed app user to ACTIVE or SUSPENDED.",
    openapi_extra=firebase_only_openapi_extra(),
)
def update_user_status(request, user_id: str, payload: schemas.UserStatusUpdateIn):
    authorize_request(
        request,
        PERM_USERS_MANAGE_PLATFORM,
        require_firebase=True,
    )
    app_user = user_services.update_user_status(user_id, payload.status)
    return success_response(request, data=_pending_user_out(app_user))


@router.patch(
    "/users/{user_id}/platform-role",
    summary="Update platform admin role",
    description="Grant or revoke the platform_admin role for a Firebase-backed app user.",
    openapi_extra=firebase_only_openapi_extra(),
)
def update_platform_role(request, user_id: str, payload: schemas.UserPlatformRoleUpdateIn):
    authorize_request(
        request,
        PERM_USERS_MANAGE_PLATFORM,
        require_firebase=True,
    )
    app_user = user_services.set_platform_admin(user_id, payload.enabled)
    return success_response(request, data=_pending_user_out(app_user))


# ---------------------------------------------------------------------------
# Facility
# ---------------------------------------------------------------------------

@router.post(
    "/facilities",
    summary="Create facility",
    description=(
        "Create a warehouse facility within the organisation, including its warehouse key. "
        "All existing org SKUs, zones, and locations are automatically mapped to it."
    ),
    openapi_extra=protected_openapi_extra(),
)
def create_facility(request, payload: schemas.FacilityCreateIn):
    authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    facility = services.create_facility(org, payload.dict(), user=user)
    return success_response(request, data=_facility_out(facility))


@router.get(
    "/facilities",
    summary="List facilities",
    description="Return all facilities for the organisation.",
    openapi_extra=protected_openapi_extra(),
)
def list_facilities(request):
    access = authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    facilities = services.list_facilities(org)
    if not access.is_api_key_bypass and access.allowed_facility_codes:
        facilities = [facility for facility in facilities if facility.code in access.allowed_facility_codes]
    return success_response(request, data=[_facility_out(f) for f in facilities])


@router.get(
    "/facilities/{code}",
    summary="Get facility",
    description="Retrieve a single facility by its code.",
    openapi_extra=protected_openapi_extra(),
)
def get_facility(request, code: str):
    access = authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request, facility_code=code)
    enforce_facility_scope(access, code)
    facility = services.get_facility(org, code)
    return success_response(request, data=_facility_out(facility))


@router.patch(
    "/facilities/{code}",
    summary="Update facility",
    description="Partially update a facility's warehouse key, name, address, or active status.",
    openapi_extra=protected_openapi_extra(),
)
def update_facility(request, code: str, payload: schemas.FacilityUpdateIn):
    access = authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request, facility_code=code)
    enforce_facility_scope(access, code)
    user = _get_user(request)
    facility = services.update_facility(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=_facility_out(facility))


# --- Facility SKU mappings ---

@router.get(
    "/facilities/{code}/skus",
    summary="List facility SKU mappings",
    description="Return all SKUs mapped to this facility, including per-facility override settings.",
    openapi_extra=protected_openapi_extra(),
)
def list_facility_skus(request, code: str):
    access = authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request, facility_code=code)
    enforce_facility_scope(access, code)
    facility = services.get_facility(org, code)
    mappings = services.list_facility_skus(facility)
    return success_response(
        request,
        data=[
            schemas.FacilitySKUOut(
                sku_code=m.sku.code,
                sku_name=m.sku.name,
                is_active=m.is_active,
                overrides=m.overrides,
            ).dict()
            for m in mappings
        ],
    )


@router.patch(
    "/facilities/{code}/skus/{sku_code}",
    summary="Update facility SKU mapping",
    description="Update the `is_active` flag or `overrides` for a SKU–facility mapping.",
    openapi_extra=protected_openapi_extra(),
)
def update_facility_sku(request, code: str, sku_code: str, payload: schemas.FacilityMappingOverrideIn):
    access = authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request, facility_code=code)
    enforce_facility_scope(access, code)
    facility = services.get_facility(org, code)
    mapping = services.update_facility_sku(facility, sku_code, payload.dict(exclude_unset=True))
    return success_response(
        request,
        data=schemas.FacilitySKUOut(
            sku_code=mapping.sku.code,
            sku_name=mapping.sku.name,
            is_active=mapping.is_active,
            overrides=mapping.overrides,
        ).dict(),
    )


# --- Facility zone mappings ---

@router.get(
    "/facilities/{code}/zones",
    summary="List facility zone mappings",
    description="Return all zones mapped to this facility.",
    openapi_extra=protected_openapi_extra(),
)
def list_facility_zones(request, code: str):
    access = authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request, facility_code=code)
    enforce_facility_scope(access, code)
    facility = services.get_facility(org, code)
    mappings = services.list_facility_zones(facility)
    return success_response(
        request,
        data=[
            schemas.FacilityZoneOut(
                zone_code=m.zone.code,
                zone_name=m.zone.name,
                is_active=m.is_active,
                overrides=m.overrides,
            ).dict()
            for m in mappings
        ],
    )


@router.patch(
    "/facilities/{code}/zones/{zone_code}",
    summary="Update facility zone mapping",
    description="Update the `is_active` flag or `overrides` for a zone–facility mapping.",
    openapi_extra=protected_openapi_extra(),
)
def update_facility_zone(request, code: str, zone_code: str, payload: schemas.FacilityMappingOverrideIn):
    access = authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request, facility_code=code)
    enforce_facility_scope(access, code)
    facility = services.get_facility(org, code)
    mapping = services.update_facility_zone(facility, zone_code, payload.dict(exclude_unset=True))
    return success_response(
        request,
        data=schemas.FacilityZoneOut(
            zone_code=mapping.zone.code,
            zone_name=mapping.zone.name,
            is_active=mapping.is_active,
            overrides=mapping.overrides,
        ).dict(),
    )


# --- Facility location mappings ---

@router.get(
    "/facilities/{code}/locations",
    summary="List facility location mappings",
    description="Return all locations mapped to this facility.",
    openapi_extra=protected_openapi_extra(),
)
def list_facility_locations(request, code: str):
    access = authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request, facility_code=code)
    enforce_facility_scope(access, code)
    facility = services.get_facility(org, code)
    mappings = services.list_facility_locations(facility)
    return success_response(
        request,
        data=[
            schemas.FacilityLocationOut(
                location_code=m.location.code,
                location_name=m.location.name,
                is_active=m.is_active,
                overrides=m.overrides,
            ).dict()
            for m in mappings
        ],
    )


@router.patch(
    "/facilities/{code}/locations/{location_code}",
    summary="Update facility location mapping",
    description="Update the `is_active` flag or `overrides` for a location–facility mapping.",
    openapi_extra=protected_openapi_extra(),
)
def update_facility_location(
    request, code: str, location_code: str, payload: schemas.FacilityMappingOverrideIn
):
    access = authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request, facility_code=code)
    enforce_facility_scope(access, code)
    facility = services.get_facility(org, code)
    mapping = services.update_facility_location(
        facility, location_code, payload.dict(exclude_unset=True)
    )
    return success_response(
        request,
        data=schemas.FacilityLocationOut(
            location_code=mapping.location.code,
            location_name=mapping.location.name,
            is_active=mapping.is_active,
            overrides=mapping.overrides,
        ).dict(),
    )


# ---------------------------------------------------------------------------
# SKU
# ---------------------------------------------------------------------------

@router.post(
    "/skus",
    summary="Create SKU",
    description=(
        "Create a new SKU within the organisation. "
        "Automatically mapped to all existing org facilities."
    ),
    openapi_extra=protected_openapi_extra(),
)
def create_sku(request, payload: schemas.SKUCreateIn):
    authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    sku = services.create_sku(org, payload.dict(), user=user)
    return success_response(request, data=_sku_out(sku))


@router.get(
    "/skus",
    summary="List SKUs",
    description="Return all SKUs for the organisation.",
    openapi_extra=protected_openapi_extra(),
)
def list_skus(request):
    authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    skus = services.list_skus(org)
    return success_response(
        request,
        data=[_sku_out(s) for s in skus],
    )


@router.get(
    "/skus/{code}",
    summary="Get SKU",
    description="Retrieve a single SKU by its code.",
    openapi_extra=protected_openapi_extra(),
)
def get_sku(request, code: str):
    authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    sku = services.get_sku(org, code)
    return success_response(request, data=_sku_out(sku))


@router.patch(
    "/skus/{code}",
    summary="Update SKU",
    description="Partially update a SKU's name, unit of measure, active status, or metadata.",
    openapi_extra=protected_openapi_extra(),
)
def update_sku(request, code: str, payload: schemas.SKUUpdateIn):
    authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    sku = services.update_sku(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=_sku_out(sku))


# ---------------------------------------------------------------------------
# Zone
# ---------------------------------------------------------------------------

@router.post(
    "/zones",
    summary="Create zone",
    description=(
        "Create a zone within the organisation. "
        "Automatically mapped to all existing org facilities."
    ),
    openapi_extra=protected_openapi_extra(),
)
def create_zone(request, payload: schemas.ZoneCreateIn):
    authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    zone = services.create_zone(org, payload.dict(), user=user)
    return success_response(request, data=_zone_out(zone))


@router.get(
    "/zones",
    summary="List zones",
    description="Return all zones for the organisation.",
    openapi_extra=protected_openapi_extra(),
)
def list_zones(request):
    authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    zones = services.list_zones(org)
    return success_response(
        request,
        data=[_zone_out(z) for z in zones],
    )


@router.get(
    "/zones/{code}",
    summary="Get zone",
    description="Retrieve a single zone by its code.",
    openapi_extra=protected_openapi_extra(),
)
def get_zone(request, code: str):
    authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    zone = services.get_zone(org, code)
    return success_response(request, data=_zone_out(zone))


@router.patch(
    "/zones/{code}",
    summary="Update zone",
    description="Partially update a zone's name or active status.",
    openapi_extra=protected_openapi_extra(),
)
def update_zone(request, code: str, payload: schemas.ZoneUpdateIn):
    authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    zone = services.update_zone(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=_zone_out(zone))


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

@router.post(
    "/locations",
    summary="Create location",
    description=(
        "Create a storage location within a zone. "
        "Automatically mapped to all existing org facilities."
    ),
    openapi_extra=protected_openapi_extra(),
)
def create_location(request, payload: schemas.LocationCreateIn):
    authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    location = services.create_location(org, payload.dict(), user=user)
    return success_response(request, data=_location_out(location))


@router.get(
    "/locations",
    summary="List locations",
    description="Return all locations for the organisation.",
    openapi_extra=protected_openapi_extra(),
)
def list_locations(request):
    authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    locations = services.list_locations(org)
    return success_response(request, data=[_location_out(loc) for loc in locations])


@router.get(
    "/locations/{code}",
    summary="Get location",
    description="Retrieve a single location by its code.",
    openapi_extra=protected_openapi_extra(),
)
def get_location(request, code: str):
    authorize_request(
        request,
        PERM_MASTERS_READ,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    location = services.get_location(org, code)
    return success_response(request, data=_location_out(location))


@router.patch(
    "/locations/{code}",
    summary="Update location",
    description="Partially update a location's name, zone, capacity, or active status.",
    openapi_extra=protected_openapi_extra(),
)
def update_location(request, code: str, payload: schemas.LocationUpdateIn):
    authorize_request(
        request,
        PERM_MASTERS_MANAGE,
        require_membership=True,
    )
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    location = services.update_location(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=_location_out(location))


# ---------------------------------------------------------------------------
# Register response schemas
# ---------------------------------------------------------------------------

register_response_schema("app_masters_routes_create_organization", _ORG_SCHEMA)
register_response_schema("app_masters_routes_list_organizations", _list_of(_ORG_SCHEMA))
register_response_schema("app_masters_routes_get_organization", _ORG_SCHEMA)
register_response_schema("app_masters_routes_update_organization", _ORG_SCHEMA)
register_response_schema("app_masters_routes_get_current_user", _CURRENT_USER_SCHEMA)
register_response_schema("app_masters_routes_list_users", _list_of(_ORG_USER_SCHEMA))
register_response_schema("app_masters_routes_create_user_grant", _USER_GRANT_SCHEMA)
register_response_schema("app_masters_routes_update_user_grant", _USER_GRANT_SCHEMA)
register_response_schema("app_masters_routes_delete_user_grant", {"type": "object", "properties": {"deleted": {"type": "boolean"}}})
register_response_schema("app_masters_routes_list_pending_users", _list_of(_PENDING_USER_SCHEMA))
register_response_schema("app_masters_routes_update_user_status", _PENDING_USER_SCHEMA)
register_response_schema("app_masters_routes_update_platform_role", _PENDING_USER_SCHEMA)
register_response_schema("app_masters_routes_create_facility", _FACILITY_SCHEMA)
register_response_schema("app_masters_routes_list_facilities", _list_of(_FACILITY_SCHEMA))
register_response_schema("app_masters_routes_get_facility", _FACILITY_SCHEMA)
register_response_schema("app_masters_routes_update_facility", _FACILITY_SCHEMA)
register_response_schema("app_masters_routes_list_facility_skus", _list_of(_FAC_SKU_SCHEMA))
register_response_schema("app_masters_routes_update_facility_sku", _FAC_SKU_SCHEMA)
register_response_schema("app_masters_routes_list_facility_zones", _list_of(_FAC_ZONE_SCHEMA))
register_response_schema("app_masters_routes_update_facility_zone", _FAC_ZONE_SCHEMA)
register_response_schema("app_masters_routes_list_facility_locations", _list_of(_FAC_LOCATION_SCHEMA))
register_response_schema("app_masters_routes_update_facility_location", _FAC_LOCATION_SCHEMA)
register_response_schema("app_masters_routes_create_sku", _SKU_SCHEMA)
register_response_schema("app_masters_routes_list_skus", _list_of(_SKU_SCHEMA))
register_response_schema("app_masters_routes_get_sku", _SKU_SCHEMA)
register_response_schema("app_masters_routes_update_sku", _SKU_SCHEMA)
register_response_schema("app_masters_routes_create_zone", _ZONE_SCHEMA)
register_response_schema("app_masters_routes_list_zones", _list_of(_ZONE_SCHEMA))
register_response_schema("app_masters_routes_get_zone", _ZONE_SCHEMA)
register_response_schema("app_masters_routes_update_zone", _ZONE_SCHEMA)
register_response_schema("app_masters_routes_create_location", _LOCATION_SCHEMA)
register_response_schema("app_masters_routes_list_locations", _list_of(_LOCATION_SCHEMA))
register_response_schema("app_masters_routes_get_location", _LOCATION_SCHEMA)
register_response_schema("app_masters_routes_update_location", _LOCATION_SCHEMA)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user(request) -> str:
    auth = getattr(request, "auth_context", None)
    if auth and auth.uid:
        return auth.uid
    if auth and auth.client_name:
        return auth.client_name
    return ""


def _facility_out(facility) -> dict:
    return schemas.FacilityOut(
        id=str(facility.id),
        code=facility.code,
        warehouse_key=facility.warehouse_key,
        name=facility.name,
        is_active=facility.is_active,
        address=facility.address,
        created_at=facility.created_at,
        updated_at=facility.updated_at,
    ).dict()


def _sku_out(sku) -> dict:
    return schemas.SKUOut(
        id=str(sku.id),
        code=sku.code,
        name=sku.name,
        unit_of_measure=sku.unit_of_measure,
        is_active=sku.is_active,
        metadata=sku.metadata,
        created_at=sku.created_at,
        updated_at=sku.updated_at,
    ).dict()


def _zone_out(zone) -> dict:
    return schemas.ZoneOut(
        id=str(zone.id),
        code=zone.code,
        name=zone.name,
        is_active=zone.is_active,
        created_at=zone.created_at,
        updated_at=zone.updated_at,
    ).dict()


def _location_out(location) -> dict:
    return schemas.LocationOut(
        id=str(location.id),
        code=location.code,
        name=location.name,
        zone_code=location.zone.code,
        is_active=location.is_active,
        capacity=location.capacity,
        created_at=location.created_at,
        updated_at=location.updated_at,
    ).dict()


def _user_grant_out(membership) -> dict:
    facility_codes = [assignment.facility.code for assignment in membership.facility_assignments.all()]
    return schemas.UserMembershipOut(
        id=str(membership.id),
        org_id=membership.org_id,
        role_code=membership.role.code,
        role_name=membership.role.name,
        status=membership.status,
        facility_codes=facility_codes,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
    ).dict()


def _platform_role_codes(app_user) -> list[str]:
    return sorted(assignment.role.code for assignment in app_user.platform_role_assignments.all())


def _org_user_out(membership) -> dict:
    app_user = membership.user
    return schemas.OrgUserOut(
        id=str(app_user.id),
        firebase_uid=app_user.firebase_uid,
        email=app_user.email,
        display_name=app_user.display_name,
        phone_number=app_user.phone_number,
        photo_url=app_user.photo_url,
        status=app_user.status,
        platform_roles=_platform_role_codes(app_user),
        grant=schemas.UserMembershipOut(**_user_grant_out(membership)),
        last_login_at=app_user.last_login_at,
        created_at=app_user.created_at,
        updated_at=app_user.updated_at,
    ).dict()


def _pending_user_out(app_user) -> dict:
    return schemas.PendingUserOut(
        id=str(app_user.id),
        firebase_uid=app_user.firebase_uid,
        email=app_user.email,
        display_name=app_user.display_name,
        phone_number=app_user.phone_number,
        photo_url=app_user.photo_url,
        status=app_user.status,
        platform_roles=_platform_role_codes(app_user),
        last_login_at=app_user.last_login_at,
        created_at=app_user.created_at,
        updated_at=app_user.updated_at,
    ).dict()


def _current_user_out(request, access) -> dict:
    app_user = access.app_user
    memberships = list(
        app_user.org_memberships.select_related("role", "org").prefetch_related("facility_assignments__facility")
    )

    return schemas.CurrentUserOut(
        id=str(app_user.id),
        firebase_uid=app_user.firebase_uid,
        email=app_user.email,
        display_name=app_user.display_name,
        phone_number=app_user.phone_number,
        photo_url=app_user.photo_url,
        status=app_user.status,
        platform_roles=_platform_role_codes(app_user),
        memberships=[schemas.UserMembershipOut(**_user_grant_out(membership)) for membership in memberships],
        effective_permissions=sorted(access.permission_codes),
        requested_org_id=access.requested_org_id,
        requested_facility_id=request.headers.get("X-Facility-Id", "").strip() or None,
        last_login_at=app_user.last_login_at,
        created_at=app_user.created_at,
        updated_at=app_user.updated_at,
    ).dict()
