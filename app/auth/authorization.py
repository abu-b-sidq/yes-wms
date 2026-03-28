from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.auth.permissions import ROLE_PLATFORM_ADMIN
from app.core.context import get_auth_context
from app.core.exceptions import AuthorizationError
from app.masters.models import (
    AppUser,
    AppUserStatus,
    MembershipStatus,
    UserOrgMembership,
)


@dataclass
class AccessContext:
    auth_source: str | None
    app_user: AppUser | None = None
    requested_org_id: str | None = None
    membership: UserOrgMembership | None = None
    permission_codes: set[str] = field(default_factory=set)
    platform_role_codes: set[str] = field(default_factory=set)
    allowed_facility_codes: set[str] = field(default_factory=set)
    is_api_key_bypass: bool = False

    @property
    def is_platform_admin(self) -> bool:
        return ROLE_PLATFORM_ADMIN in self.platform_role_codes


def authorize_request(
    request: Any,
    permission_code: str | None = None,
    *,
    org_id: str | None = None,
    require_firebase: bool = False,
    allow_pending: bool = False,
    allow_suspended: bool = False,
    require_membership: bool = False,
    require_optional_facility_header: bool = False,
) -> AccessContext:
    auth = get_auth_context(request)
    if auth.auth_source != "firebase":
        if require_firebase:
            raise AuthorizationError(
                "Firebase authentication is required for this route.",
                code="AUTHZ_FIREBASE_REQUIRED",
            )
        return AccessContext(
            auth_source=auth.auth_source,
            is_api_key_bypass=auth.auth_source == "api_key",
        )

    requested_org_id = org_id or request.headers.get("X-Org-Id", "").strip() or None
    context = _build_access_context(request, requested_org_id)

    if context.app_user is None:
        raise AuthorizationError(
            "Unable to resolve the authenticated application user.",
            code="AUTHZ_FORBIDDEN",
        )

    if context.app_user.status == AppUserStatus.PENDING and not allow_pending:
        raise AuthorizationError(
            "User access is pending approval.",
            code="AUTHZ_PENDING_USER",
        )

    if context.app_user.status == AppUserStatus.SUSPENDED and not allow_suspended:
        raise AuthorizationError(
            "User access has been suspended.",
            code="AUTHZ_SUSPENDED_USER",
        )

    if require_membership and requested_org_id and not context.is_platform_admin:
        membership = context.membership
        if membership is None or membership.status != MembershipStatus.ACTIVE:
            raise AuthorizationError(
                "You do not have access to this organization.",
                code="AUTHZ_FORBIDDEN",
            )

    if permission_code and permission_code not in context.permission_codes:
        raise AuthorizationError(
            "You do not have permission to perform this action.",
            code="AUTHZ_FORBIDDEN",
        )

    facility_code = request.headers.get("X-Facility-Id", "").strip()
    if context.allowed_facility_codes:
        if require_optional_facility_header and not facility_code:
            raise AuthorizationError(
                "Facility-restricted users must provide `X-Facility-Id` for this route.",
                code="AUTHZ_FACILITY_SCOPE_REQUIRED",
            )
        if facility_code and facility_code not in context.allowed_facility_codes:
            raise AuthorizationError(
                "You do not have access to the requested facility.",
                code="AUTHZ_FORBIDDEN",
            )

    return context


def enforce_facility_scope(access: AccessContext, facility_code: str) -> None:
    if access.allowed_facility_codes and facility_code not in access.allowed_facility_codes:
        raise AuthorizationError(
            "You do not have access to the requested facility.",
            code="AUTHZ_FORBIDDEN",
        )


def get_mcp_access_context(uid: str, org_id: str | None) -> AccessContext:
    """Build an AccessContext from a Firebase UID for use in MCP tools (no HTTP request)."""
    from app.core.context import AuthContext

    auth = AuthContext(is_authenticated=True, auth_source="firebase", uid=uid)

    class _Req:
        def __init__(self):
            self.auth_context = auth
            self._authz_context_cache: dict = {}

    context = _build_access_context(_Req(), org_id)
    if context.app_user is None:
        raise AuthorizationError("Unable to resolve authenticated user.", code="AUTHZ_FORBIDDEN")
    if context.app_user.status == AppUserStatus.PENDING:
        raise AuthorizationError("User access is pending approval.", code="AUTHZ_PENDING_USER")
    if context.app_user.status == AppUserStatus.SUSPENDED:
        raise AuthorizationError("User access has been suspended.", code="AUTHZ_SUSPENDED_USER")
    return context


def active_membership_org_ids(app_user: AppUser) -> set[str]:
    return set(
        UserOrgMembership.objects.filter(
            user=app_user,
            status=MembershipStatus.ACTIVE,
        ).values_list("org_id", flat=True)
    )


def _build_access_context(request: Any, org_id: str | None) -> AccessContext:
    cache = getattr(request, "_authz_context_cache", None)
    if cache is None:
        cache = {}
        request._authz_context_cache = cache

    cache_key = org_id or ""
    if cache_key in cache:
        return cache[cache_key]

    auth = get_auth_context(request)
    app_user = _load_app_user(auth)
    if app_user is None:
        context = AccessContext(auth_source=auth.auth_source)
        cache[cache_key] = context
        return context

    platform_assignments = list(
        app_user.platform_role_assignments.select_related("role").prefetch_related("role__permissions")
    )
    platform_role_codes = {assignment.role.code for assignment in platform_assignments}
    permission_codes = {
        permission.code
        for assignment in platform_assignments
        for permission in assignment.role.permissions.all()
    }

    membership = None
    allowed_facility_codes: set[str] = set()
    if org_id:
        membership = (
            app_user.org_memberships.filter(org_id=org_id)
            .select_related("role", "org")
            .prefetch_related("role__permissions", "facility_assignments__facility")
            .first()
        )
        if membership and membership.status == MembershipStatus.ACTIVE:
            permission_codes.update(permission.code for permission in membership.role.permissions.all())
            allowed_facility_codes = {
                assignment.facility.code for assignment in membership.facility_assignments.all()
            }

    context = AccessContext(
        auth_source=auth.auth_source,
        app_user=app_user,
        requested_org_id=org_id,
        membership=membership,
        permission_codes=permission_codes,
        platform_role_codes=platform_role_codes,
        allowed_facility_codes=allowed_facility_codes,
    )
    cache[cache_key] = context
    return context


def _load_app_user(auth) -> AppUser | None:
    if auth.app_user_id:
        try:
            return AppUser.objects.get(id=auth.app_user_id)
        except AppUser.DoesNotExist:
            return None

    if auth.uid:
        try:
            return AppUser.objects.get(firebase_uid=auth.uid)
        except AppUser.DoesNotExist:
            return None

    return None

