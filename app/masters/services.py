from django.db import IntegrityError
from django.db.models import Q

from app.core.exceptions import EntityNotFoundError, ValidationError
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


# --- Organization ---

def create_organization(data: dict) -> Organization:
    try:
        return Organization.objects.create(**data)
    except IntegrityError:
        raise ValidationError(f"Organization '{data['id']}' already exists.")


def get_organization(org_id: str) -> Organization:
    try:
        return Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        raise EntityNotFoundError(f"Organization '{org_id}' not found.")


def update_organization(org_id: str, data: dict) -> Organization:
    org = get_organization(org_id)
    for key, value in data.items():
        if value is not None:
            setattr(org, key, value)
    org.save()
    return org


def list_organizations() -> list[Organization]:
    return list(Organization.objects.all().order_by("id"))


# --- Facility ---

def create_facility(org: Organization, data: dict, user: str = "") -> Facility:
    try:
        return Facility.objects.create(
            org=org, created_by=user, updated_by=user, **data
        )
    except IntegrityError:
        raise ValidationError(
            "Facility code or warehouse key already exists in "
            f"org '{org.id}'."
        )


def get_facility(org: Organization, code: str) -> Facility:
    try:
        return Facility.objects.get(org=org, code=code)
    except Facility.DoesNotExist:
        raise EntityNotFoundError(f"Facility '{code}' not found in org '{org.id}'.")


def update_facility(org: Organization, code: str, data: dict, user: str = "") -> Facility:
    facility = get_facility(org, code)
    for key, value in data.items():
        if value is not None:
            setattr(facility, key, value)
    facility.updated_by = user
    try:
        facility.save()
    except IntegrityError:
        raise ValidationError(
            "Facility code or warehouse key already exists in "
            f"org '{org.id}'."
        )
    return facility


def list_facilities(org: Organization) -> list[Facility]:
    return list(Facility.objects.filter(org=org).order_by("code"))


# --- SKU ---

def create_sku(org: Organization, data: dict, user: str = "") -> SKU:
    try:
        return SKU.objects.create(org=org, created_by=user, updated_by=user, **data)
    except IntegrityError:
        raise ValidationError(
            f"SKU with code '{data.get('code')}' already exists in org '{org.id}'."
        )


def get_sku(org: Organization, code: str) -> SKU:
    try:
        return SKU.objects.get(org=org, code=code)
    except SKU.DoesNotExist:
        raise EntityNotFoundError(f"SKU '{code}' not found in org '{org.id}'.")


def update_sku(org: Organization, code: str, data: dict, user: str = "") -> SKU:
    sku = get_sku(org, code)
    for key, value in data.items():
        if value is not None:
            setattr(sku, key, value)
    sku.updated_by = user
    sku.save()
    return sku


def list_skus(org: Organization, search: str = "") -> list[SKU]:
    queryset = SKU.objects.filter(org=org)
    if search:
        term = search.strip()
        queryset = queryset.filter(
            Q(code__icontains=term) | Q(name__icontains=term)
        )
    return list(queryset.order_by("code"))


# --- Zone ---

def create_zone(org: Organization, data: dict, user: str = "") -> Zone:
    try:
        return Zone.objects.create(org=org, created_by=user, updated_by=user, **data)
    except IntegrityError:
        raise ValidationError(
            f"Zone with code '{data.get('code')}' already exists in org '{org.id}'."
        )


def get_zone(org: Organization, code: str) -> Zone:
    try:
        return Zone.objects.get(org=org, code=code)
    except Zone.DoesNotExist:
        raise EntityNotFoundError(f"Zone '{code}' not found in org '{org.id}'.")


def update_zone(org: Organization, code: str, data: dict, user: str = "") -> Zone:
    zone = get_zone(org, code)
    for key, value in data.items():
        if value is not None:
            setattr(zone, key, value)
    zone.updated_by = user
    zone.save()
    return zone


def list_zones(org: Organization) -> list[Zone]:
    return list(Zone.objects.filter(org=org).order_by("code"))


# --- Location ---

def create_location(org: Organization, data: dict, user: str = "") -> Location:
    zone_code = data.pop("zone_code")
    zone = get_zone(org, zone_code)
    try:
        return Location.objects.create(
            org=org, zone=zone, created_by=user, updated_by=user, **data
        )
    except IntegrityError:
        raise ValidationError(
            f"Location with code '{data.get('code')}' already exists in org '{org.id}'."
        )


def get_location(org: Organization, code: str) -> Location:
    try:
        return Location.objects.select_related("zone").get(org=org, code=code)
    except Location.DoesNotExist:
        raise EntityNotFoundError(f"Location '{code}' not found in org '{org.id}'.")


def update_location(
    org: Organization, code: str, data: dict, user: str = ""
) -> Location:
    location = get_location(org, code)
    zone_code = data.pop("zone_code", None)
    if zone_code is not None:
        location.zone = get_zone(org, zone_code)
    for key, value in data.items():
        if value is not None:
            setattr(location, key, value)
    location.updated_by = user
    location.save()
    return location


def list_locations(org: Organization) -> list[Location]:
    return list(Location.objects.filter(org=org).select_related("zone").order_by("code"))


# --- Facility Mapping Overrides ---

def list_facility_skus(facility: Facility) -> list[FacilitySKU]:
    return list(
        FacilitySKU.objects.filter(facility=facility)
        .select_related("sku")
        .order_by("sku__code")
    )


def update_facility_sku(
    facility: Facility, sku_code: str, data: dict
) -> FacilitySKU:
    try:
        mapping = FacilitySKU.objects.select_related("sku").get(
            facility=facility, sku__code=sku_code
        )
    except FacilitySKU.DoesNotExist:
        raise EntityNotFoundError(
            f"SKU '{sku_code}' is not mapped to facility '{facility.code}'."
        )
    if "is_active" in data and data["is_active"] is not None:
        mapping.is_active = data["is_active"]
    if "overrides" in data and data["overrides"] is not None:
        mapping.overrides = data["overrides"]
    mapping.save()
    return mapping


def list_facility_zones(facility: Facility) -> list[FacilityZone]:
    return list(
        FacilityZone.objects.filter(facility=facility)
        .select_related("zone")
        .order_by("zone__code")
    )


def update_facility_zone(
    facility: Facility, zone_code: str, data: dict
) -> FacilityZone:
    try:
        mapping = FacilityZone.objects.select_related("zone").get(
            facility=facility, zone__code=zone_code
        )
    except FacilityZone.DoesNotExist:
        raise EntityNotFoundError(
            f"Zone '{zone_code}' is not mapped to facility '{facility.code}'."
        )
    if "is_active" in data and data["is_active"] is not None:
        mapping.is_active = data["is_active"]
    if "overrides" in data and data["overrides"] is not None:
        mapping.overrides = data["overrides"]
    mapping.save()
    return mapping


def list_facility_locations(facility: Facility) -> list[FacilityLocation]:
    return list(
        FacilityLocation.objects.filter(facility=facility)
        .select_related("location")
        .order_by("location__code")
    )


def update_facility_location(
    facility: Facility, location_code: str, data: dict
) -> FacilityLocation:
    try:
        mapping = FacilityLocation.objects.select_related("location").get(
            facility=facility, location__code=location_code
        )
    except FacilityLocation.DoesNotExist:
        raise EntityNotFoundError(
            f"Location '{location_code}' is not mapped to facility '{facility.code}'."
        )
    if "is_active" in data and data["is_active"] is not None:
        mapping.is_active = data["is_active"]
    if "overrides" in data and data["overrides"] is not None:
        mapping.overrides = data["overrides"]
    mapping.save()
    return mapping
