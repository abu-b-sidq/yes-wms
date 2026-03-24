from ninja import Router

from app.core.openapi import protected_openapi_extra, success_response_schema
from app.core.response import success_response
from app.core.tenant import resolve_request_tenant
from app.masters import schemas, services

router = Router(tags=["masters"])

# ---------------------------------------------------------------------------
# Response schemas
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

_MAPPING_OVERRIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "is_active": {"type": "boolean"},
        "overrides": {"type": "object"},
    },
}


def _list_of(schema: dict) -> dict:
    return {"type": "array", "items": schema}


ORGLESS_PROTECTED = protected_openapi_extra(require_org=False)
ORG_PROTECTED = protected_openapi_extra()


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------

@router.post(
    "/organizations",
    summary="Create organization",
    description="Create a new top-level organisation. The `id` is chosen by the caller and must be unique.",
    openapi_extra=protected_openapi_extra(
        require_org=False,
        response_schema=success_response_schema(_ORG_SCHEMA),
    ),
)
def create_organization(request, payload: schemas.OrganizationCreateIn):
    org = services.create_organization(payload.dict())
    return success_response(request, data=schemas.OrganizationOut.from_orm(org).dict())


@router.get(
    "/organizations",
    summary="List organizations",
    description="Return all organisations visible to the authenticated warehouse.",
    openapi_extra=protected_openapi_extra(
        require_org=False,
        response_schema=success_response_schema(_list_of(_ORG_SCHEMA)),
    ),
)
def list_organizations(request):
    orgs = services.list_organizations()
    return success_response(
        request,
        data=[schemas.OrganizationOut.from_orm(o).dict() for o in orgs],
    )


@router.get(
    "/organizations/{org_id}",
    summary="Get organization",
    description="Retrieve a single organisation by its ID.",
    openapi_extra=protected_openapi_extra(
        require_org=False,
        response_schema=success_response_schema(_ORG_SCHEMA),
    ),
)
def get_organization(request, org_id: str):
    org = services.get_organization(org_id)
    return success_response(request, data=schemas.OrganizationOut.from_orm(org).dict())


@router.patch(
    "/organizations/{org_id}",
    summary="Update organization",
    description="Partially update an organisation's name or active status.",
    openapi_extra=protected_openapi_extra(
        require_org=False,
        response_schema=success_response_schema(_ORG_SCHEMA),
    ),
)
def update_organization(request, org_id: str, payload: schemas.OrganizationUpdateIn):
    org = services.update_organization(org_id, payload.dict(exclude_unset=True))
    return success_response(request, data=schemas.OrganizationOut.from_orm(org).dict())


# ---------------------------------------------------------------------------
# Facility
# ---------------------------------------------------------------------------

@router.post(
    "/facilities",
    summary="Create facility",
    description=(
        "Create a new warehouse facility within the organisation. "
        "Creating a facility automatically maps all existing org-level SKUs, zones, and locations to it."
    ),
    openapi_extra=protected_openapi_extra(response_schema=success_response_schema(_FACILITY_SCHEMA)),
)
def create_facility(request, payload: schemas.FacilityCreateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    facility = services.create_facility(org, payload.dict(), user=user)
    return success_response(request, data=_facility_out(facility))


@router.get(
    "/facilities",
    summary="List facilities",
    description="Return all facilities for the organisation.",
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_list_of(_FACILITY_SCHEMA))
    ),
)
def list_facilities(request):
    org, _ = resolve_request_tenant(request)
    facilities = services.list_facilities(org)
    return success_response(request, data=[_facility_out(f) for f in facilities])


@router.get(
    "/facilities/{code}",
    summary="Get facility",
    description="Retrieve a single facility by its code.",
    openapi_extra=protected_openapi_extra(response_schema=success_response_schema(_FACILITY_SCHEMA)),
)
def get_facility(request, code: str):
    org, _ = resolve_request_tenant(request)
    facility = services.get_facility(org, code)
    return success_response(request, data=_facility_out(facility))


@router.patch(
    "/facilities/{code}",
    summary="Update facility",
    description="Partially update a facility's name, address, or active status.",
    openapi_extra=protected_openapi_extra(response_schema=success_response_schema(_FACILITY_SCHEMA)),
)
def update_facility(request, code: str, payload: schemas.FacilityUpdateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    facility = services.update_facility(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=_facility_out(facility))


# ---------------------------------------------------------------------------
# Facility Mapping Overrides
# ---------------------------------------------------------------------------

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


@router.get(
    "/facilities/{code}/skus",
    summary="List facility SKU mappings",
    description="Return all SKUs mapped to this facility, including per-facility override settings.",
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_list_of(_FAC_SKU_SCHEMA))
    ),
)
def list_facility_skus(request, code: str):
    org, _ = resolve_request_tenant(request)
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
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_FAC_SKU_SCHEMA)
    ),
)
def update_facility_sku(request, code: str, sku_code: str, payload: schemas.FacilityMappingOverrideIn):
    org, _ = resolve_request_tenant(request)
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


@router.get(
    "/facilities/{code}/zones",
    summary="List facility zone mappings",
    description="Return all zones mapped to this facility.",
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_list_of(_FAC_ZONE_SCHEMA))
    ),
)
def list_facility_zones(request, code: str):
    org, _ = resolve_request_tenant(request)
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
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_FAC_ZONE_SCHEMA)
    ),
)
def update_facility_zone(request, code: str, zone_code: str, payload: schemas.FacilityMappingOverrideIn):
    org, _ = resolve_request_tenant(request)
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


@router.get(
    "/facilities/{code}/locations",
    summary="List facility location mappings",
    description="Return all locations mapped to this facility.",
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_list_of(_FAC_LOCATION_SCHEMA))
    ),
)
def list_facility_locations(request, code: str):
    org, _ = resolve_request_tenant(request)
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
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_FAC_LOCATION_SCHEMA)
    ),
)
def update_facility_location(
    request, code: str, location_code: str, payload: schemas.FacilityMappingOverrideIn
):
    org, _ = resolve_request_tenant(request)
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
        "Create a new Stock Keeping Unit within the organisation. "
        "Creating a SKU automatically maps it to all existing org facilities."
    ),
    openapi_extra=protected_openapi_extra(response_schema=success_response_schema(_SKU_SCHEMA)),
)
def create_sku(request, payload: schemas.SKUCreateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    sku = services.create_sku(org, payload.dict(), user=user)
    return success_response(request, data=schemas.SKUOut.from_orm(sku).dict())


@router.get(
    "/skus",
    summary="List SKUs",
    description="Return all SKUs for the organisation.",
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_list_of(_SKU_SCHEMA))
    ),
)
def list_skus(request):
    org, _ = resolve_request_tenant(request)
    skus = services.list_skus(org)
    return success_response(
        request,
        data=[schemas.SKUOut.from_orm(s).dict() for s in skus],
    )


@router.get(
    "/skus/{code}",
    summary="Get SKU",
    description="Retrieve a single SKU by its code.",
    openapi_extra=protected_openapi_extra(response_schema=success_response_schema(_SKU_SCHEMA)),
)
def get_sku(request, code: str):
    org, _ = resolve_request_tenant(request)
    sku = services.get_sku(org, code)
    return success_response(request, data=schemas.SKUOut.from_orm(sku).dict())


@router.patch(
    "/skus/{code}",
    summary="Update SKU",
    description="Partially update a SKU's name, unit of measure, active status, or metadata.",
    openapi_extra=protected_openapi_extra(response_schema=success_response_schema(_SKU_SCHEMA)),
)
def update_sku(request, code: str, payload: schemas.SKUUpdateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    sku = services.update_sku(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=schemas.SKUOut.from_orm(sku).dict())


# ---------------------------------------------------------------------------
# Zone
# ---------------------------------------------------------------------------

@router.post(
    "/zones",
    summary="Create zone",
    description=(
        "Create a new zone within the organisation. "
        "Creating a zone automatically maps it to all existing org facilities."
    ),
    openapi_extra=protected_openapi_extra(response_schema=success_response_schema(_ZONE_SCHEMA)),
)
def create_zone(request, payload: schemas.ZoneCreateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    zone = services.create_zone(org, payload.dict(), user=user)
    return success_response(request, data=schemas.ZoneOut.from_orm(zone).dict())


@router.get(
    "/zones",
    summary="List zones",
    description="Return all zones for the organisation.",
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_list_of(_ZONE_SCHEMA))
    ),
)
def list_zones(request):
    org, _ = resolve_request_tenant(request)
    zones = services.list_zones(org)
    return success_response(
        request,
        data=[schemas.ZoneOut.from_orm(z).dict() for z in zones],
    )


@router.get(
    "/zones/{code}",
    summary="Get zone",
    description="Retrieve a single zone by its code.",
    openapi_extra=protected_openapi_extra(response_schema=success_response_schema(_ZONE_SCHEMA)),
)
def get_zone(request, code: str):
    org, _ = resolve_request_tenant(request)
    zone = services.get_zone(org, code)
    return success_response(request, data=schemas.ZoneOut.from_orm(zone).dict())


@router.patch(
    "/zones/{code}",
    summary="Update zone",
    description="Partially update a zone's name or active status.",
    openapi_extra=protected_openapi_extra(response_schema=success_response_schema(_ZONE_SCHEMA)),
)
def update_zone(request, code: str, payload: schemas.ZoneUpdateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    zone = services.update_zone(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=schemas.ZoneOut.from_orm(zone).dict())


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

@router.post(
    "/locations",
    summary="Create location",
    description=(
        "Create a new storage location within a zone. "
        "Creating a location automatically maps it to all existing org facilities."
    ),
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_LOCATION_SCHEMA)
    ),
)
def create_location(request, payload: schemas.LocationCreateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    location = services.create_location(org, payload.dict(), user=user)
    return success_response(request, data=_location_out(location))


@router.get(
    "/locations",
    summary="List locations",
    description="Return all locations for the organisation.",
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_list_of(_LOCATION_SCHEMA))
    ),
)
def list_locations(request):
    org, _ = resolve_request_tenant(request)
    locations = services.list_locations(org)
    return success_response(request, data=[_location_out(loc) for loc in locations])


@router.get(
    "/locations/{code}",
    summary="Get location",
    description="Retrieve a single location by its code.",
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_LOCATION_SCHEMA)
    ),
)
def get_location(request, code: str):
    org, _ = resolve_request_tenant(request)
    location = services.get_location(org, code)
    return success_response(request, data=_location_out(location))


@router.patch(
    "/locations/{code}",
    summary="Update location",
    description="Partially update a location's name, zone, capacity, or active status.",
    openapi_extra=protected_openapi_extra(
        response_schema=success_response_schema(_LOCATION_SCHEMA)
    ),
)
def update_location(request, code: str, payload: schemas.LocationUpdateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    location = services.update_location(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=_location_out(location))


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
        name=facility.name,
        is_active=facility.is_active,
        address=facility.address,
        created_at=facility.created_at,
        updated_at=facility.updated_at,
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
