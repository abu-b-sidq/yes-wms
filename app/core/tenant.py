from app.core.context import TenantContext
from app.core.exceptions import TenantResolutionError


def resolve_request_tenant(request, *, require_facility: bool = False):
    """Resolve org and optionally facility from standalone request headers."""
    from app.masters.models import Facility, Organization

    org_id = request.headers.get("X-Org-Id", "").strip()
    facility_code = request.headers.get("X-Facility-Id", "").strip()

    if not org_id:
        raise TenantResolutionError("Missing required `X-Org-Id` header.")

    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist as exc:
        raise TenantResolutionError(f"Organization '{org_id}' not found.") from exc

    facility = None
    if facility_code:
        try:
            facility = Facility.objects.get(org=org, code=facility_code)
        except Facility.DoesNotExist as exc:
            raise TenantResolutionError(
                f"Facility '{facility_code}' not found in org '{org_id}'."
            ) from exc
    elif require_facility:
        raise TenantResolutionError("Missing required `X-Facility-Id` header.")

    tenant_context = getattr(request, "tenant_context", None)
    if tenant_context is None:
        tenant_context = TenantContext()
        request.tenant_context = tenant_context
    tenant_context.org_id = org.id
    tenant_context.facility_id = facility.code if facility else None

    return org, facility
