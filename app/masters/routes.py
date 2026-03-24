from ninja import Router

from app.core.openapi import protected_openapi_extra
from app.core.response import success_response
from app.core.tenant import resolve_request_tenant
from app.masters import schemas, services

router = Router(tags=["masters"])
ORGLESS_PROTECTED = protected_openapi_extra(require_org=False)
ORG_PROTECTED = protected_openapi_extra()


# --- Organization ---

@router.post(
    "/organizations",
    summary="Create organization",
    openapi_extra=ORGLESS_PROTECTED,
)
def create_organization(request, payload: schemas.OrganizationCreateIn):
    org = services.create_organization(payload.dict())
    return success_response(request, data=schemas.OrganizationOut.from_orm(org).dict())


@router.get(
    "/organizations",
    summary="List organizations",
    openapi_extra=ORGLESS_PROTECTED,
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
    openapi_extra=ORGLESS_PROTECTED,
)
def get_organization(request, org_id: str):
    org = services.get_organization(org_id)
    return success_response(request, data=schemas.OrganizationOut.from_orm(org).dict())


@router.patch(
    "/organizations/{org_id}",
    summary="Update organization",
    openapi_extra=ORGLESS_PROTECTED,
)
def update_organization(request, org_id: str, payload: schemas.OrganizationUpdateIn):
    org = services.update_organization(org_id, payload.dict(exclude_unset=True))
    return success_response(request, data=schemas.OrganizationOut.from_orm(org).dict())


# --- Facility ---

@router.post("/facilities", summary="Create facility", openapi_extra=ORG_PROTECTED)
def create_facility(request, payload: schemas.FacilityCreateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    facility = services.create_facility(org, payload.dict(), user=user)
    return success_response(request, data=_facility_out(facility))


@router.get("/facilities", summary="List facilities", openapi_extra=ORG_PROTECTED)
def list_facilities(request):
    org, _ = resolve_request_tenant(request)
    facilities = services.list_facilities(org)
    return success_response(request, data=[_facility_out(f) for f in facilities])


@router.get("/facilities/{code}", summary="Get facility", openapi_extra=ORG_PROTECTED)
def get_facility(request, code: str):
    org, _ = resolve_request_tenant(request)
    facility = services.get_facility(org, code)
    return success_response(request, data=_facility_out(facility))


@router.patch("/facilities/{code}", summary="Update facility", openapi_extra=ORG_PROTECTED)
def update_facility(request, code: str, payload: schemas.FacilityUpdateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    facility = services.update_facility(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=_facility_out(facility))


# --- Facility Mapping Overrides ---

@router.get(
    "/facilities/{code}/skus",
    summary="List facility SKU mappings",
    openapi_extra=ORG_PROTECTED,
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
    openapi_extra=ORG_PROTECTED,
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
    openapi_extra=ORG_PROTECTED,
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
    openapi_extra=ORG_PROTECTED,
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
    openapi_extra=ORG_PROTECTED,
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
    openapi_extra=ORG_PROTECTED,
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


# --- SKU ---

@router.post("/skus", summary="Create SKU", openapi_extra=ORG_PROTECTED)
def create_sku(request, payload: schemas.SKUCreateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    sku = services.create_sku(org, payload.dict(), user=user)
    return success_response(request, data=schemas.SKUOut.from_orm(sku).dict())


@router.get("/skus", summary="List SKUs", openapi_extra=ORG_PROTECTED)
def list_skus(request):
    org, _ = resolve_request_tenant(request)
    skus = services.list_skus(org)
    return success_response(
        request,
        data=[schemas.SKUOut.from_orm(s).dict() for s in skus],
    )


@router.get("/skus/{code}", summary="Get SKU", openapi_extra=ORG_PROTECTED)
def get_sku(request, code: str):
    org, _ = resolve_request_tenant(request)
    sku = services.get_sku(org, code)
    return success_response(request, data=schemas.SKUOut.from_orm(sku).dict())


@router.patch("/skus/{code}", summary="Update SKU", openapi_extra=ORG_PROTECTED)
def update_sku(request, code: str, payload: schemas.SKUUpdateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    sku = services.update_sku(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=schemas.SKUOut.from_orm(sku).dict())


# --- Zone ---

@router.post("/zones", summary="Create zone", openapi_extra=ORG_PROTECTED)
def create_zone(request, payload: schemas.ZoneCreateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    zone = services.create_zone(org, payload.dict(), user=user)
    return success_response(request, data=schemas.ZoneOut.from_orm(zone).dict())


@router.get("/zones", summary="List zones", openapi_extra=ORG_PROTECTED)
def list_zones(request):
    org, _ = resolve_request_tenant(request)
    zones = services.list_zones(org)
    return success_response(
        request,
        data=[schemas.ZoneOut.from_orm(z).dict() for z in zones],
    )


@router.get("/zones/{code}", summary="Get zone", openapi_extra=ORG_PROTECTED)
def get_zone(request, code: str):
    org, _ = resolve_request_tenant(request)
    zone = services.get_zone(org, code)
    return success_response(request, data=schemas.ZoneOut.from_orm(zone).dict())


@router.patch("/zones/{code}", summary="Update zone", openapi_extra=ORG_PROTECTED)
def update_zone(request, code: str, payload: schemas.ZoneUpdateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    zone = services.update_zone(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=schemas.ZoneOut.from_orm(zone).dict())


# --- Location ---

@router.post("/locations", summary="Create location", openapi_extra=ORG_PROTECTED)
def create_location(request, payload: schemas.LocationCreateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    location = services.create_location(org, payload.dict(), user=user)
    return success_response(request, data=_location_out(location))


@router.get("/locations", summary="List locations", openapi_extra=ORG_PROTECTED)
def list_locations(request):
    org, _ = resolve_request_tenant(request)
    locations = services.list_locations(org)
    return success_response(request, data=[_location_out(loc) for loc in locations])


@router.get("/locations/{code}", summary="Get location", openapi_extra=ORG_PROTECTED)
def get_location(request, code: str):
    org, _ = resolve_request_tenant(request)
    location = services.get_location(org, code)
    return success_response(request, data=_location_out(location))


@router.patch("/locations/{code}", summary="Update location", openapi_extra=ORG_PROTECTED)
def update_location(request, code: str, payload: schemas.LocationUpdateIn):
    org, _ = resolve_request_tenant(request)
    user = _get_user(request)
    location = services.update_location(org, code, payload.dict(exclude_unset=True), user=user)
    return success_response(request, data=_location_out(location))


# --- Helpers ---

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
