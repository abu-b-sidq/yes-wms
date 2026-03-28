from __future__ import annotations

from app.core.context import TenantContext
from app.core.exceptions import TenantResolutionError


def resolve_request_tenant(
    request,
    *,
    require_facility: bool = False,
    facility_code: str | None = None,
):
    """Resolve org and optionally facility from standalone request headers."""
    from app.masters.models import Facility, Organization

    org_id = request.headers.get("X-Org-Id", "").strip()
    requested_facility_code = request.headers.get("X-Facility-Id", "").strip()
    warehouse_key = request.headers.get("warehouse", "").strip()
    effective_facility_code = facility_code or requested_facility_code

    if not org_id:
        raise TenantResolutionError("Missing required `X-Org-Id` header.")
    if facility_code and requested_facility_code and requested_facility_code != facility_code:
        raise TenantResolutionError(
            "Path facility code does not match `X-Facility-Id` header."
        )

    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist as exc:
        raise TenantResolutionError(f"Organization '{org_id}' not found.") from exc

    facility = None
    facilities = Facility.objects.filter(org=org)
    if effective_facility_code:
        try:
            facility = facilities.get(code=effective_facility_code)
        except Facility.DoesNotExist as exc:
            raise TenantResolutionError(
                f"Facility '{effective_facility_code}' not found in org '{org_id}'."
            ) from exc
        if facility.warehouse_key != warehouse_key:
            raise TenantResolutionError(
                f"Warehouse '{warehouse_key}' is not assigned to facility '{effective_facility_code}' in org '{org_id}'."
            )
    elif require_facility:
        raise TenantResolutionError("Missing required `X-Facility-Id` header.")
    elif facilities.exists() and not facilities.filter(warehouse_key=warehouse_key).exists():
        raise TenantResolutionError(
            f"Warehouse '{warehouse_key}' is not assigned to org '{org_id}'."
        )

    tenant_context = getattr(request, "tenant_context", None)
    if tenant_context is None:
        tenant_context = TenantContext()
        request.tenant_context = tenant_context
    tenant_context.org_id = org.id
    tenant_context.facility_id = facility.code if facility else None

    return org, facility
