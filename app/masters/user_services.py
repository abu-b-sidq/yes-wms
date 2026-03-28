from __future__ import annotations

from django.db import transaction

from app.auth.permissions import ROLE_PLATFORM_ADMIN
from app.core.exceptions import AuthorizationError, EntityNotFoundError, ValidationError
from app.masters.models import (
    AppUser,
    AppUserStatus,
    Facility,
    MembershipStatus,
    Organization,
    Role,
    RoleScope,
    UserMembershipFacility,
    UserOrgMembership,
    UserPlatformRole,
)


def normalize_email(value: str) -> str:
    return value.strip().lower()


def get_app_user(user_id: str) -> AppUser:
    try:
        return AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        raise EntityNotFoundError(f"User '{user_id}' not found.")


def list_org_users(org: Organization) -> list[UserOrgMembership]:
    return list(
        UserOrgMembership.objects.filter(org=org)
        .select_related("user", "role", "org")
        .prefetch_related("facility_assignments__facility", "user__platform_role_assignments__role")
        .order_by("user__email", "user__firebase_uid")
    )


def list_pending_users() -> list[AppUser]:
    return list(
        AppUser.objects.filter(status=AppUserStatus.PENDING, org_memberships__isnull=True)
        .prefetch_related("platform_role_assignments__role")
        .order_by("created_at")
    )


def list_user_organizations(app_user: AppUser) -> list[Organization]:
    return list(
        Organization.objects.filter(
            user_memberships__user=app_user,
            user_memberships__status=MembershipStatus.ACTIVE,
        )
        .distinct()
        .order_by("id")
    )


@transaction.atomic
def grant_org_access(
    org: Organization,
    *,
    email: str,
    role_code: str,
    facility_codes: list[str] | None = None,
) -> UserOrgMembership:
    normalized_email = normalize_email(email)
    if not normalized_email:
        raise ValidationError("`email` is required.")

    try:
        app_user = AppUser.objects.get(email=normalized_email)
    except AppUser.DoesNotExist:
        raise AuthorizationError(
            "User must log in with Firebase before access can be granted.",
            code="AUTHZ_USER_LOGIN_REQUIRED",
            status_code=400,
        )

    if UserOrgMembership.objects.filter(user=app_user, org=org).exists():
        raise ValidationError(
            f"User '{normalized_email}' already has access to organization '{org.id}'."
        )

    membership = UserOrgMembership.objects.create(
        user=app_user,
        org=org,
        role=_get_org_role(role_code),
        status=MembershipStatus.ACTIVE,
    )
    _set_membership_facilities(membership, org, facility_codes)

    if app_user.status == AppUserStatus.PENDING:
        app_user.status = AppUserStatus.ACTIVE
        app_user.save(update_fields=["status", "updated_at"])

    return _membership_with_related(membership.id)


@transaction.atomic
def update_org_access(
    org: Organization,
    *,
    user_id: str,
    grant_id: str,
    role_code: str | None = None,
    status: str | None = None,
    facility_codes: list[str] | None = None,
) -> UserOrgMembership:
    membership = _get_membership(org, user_id=user_id, grant_id=grant_id)

    if role_code is not None:
        membership.role = _get_org_role(role_code)
    if status is not None:
        membership.status = _normalize_membership_status(status)

    membership.save(update_fields=["role", "status", "updated_at"])

    if facility_codes is not None:
        _set_membership_facilities(membership, org, facility_codes)

    if membership.status == MembershipStatus.ACTIVE and membership.user.status == AppUserStatus.PENDING:
        membership.user.status = AppUserStatus.ACTIVE
        membership.user.save(update_fields=["status", "updated_at"])

    return _membership_with_related(membership.id)


@transaction.atomic
def delete_org_access(org: Organization, *, user_id: str, grant_id: str) -> None:
    membership = _get_membership(org, user_id=user_id, grant_id=grant_id)
    membership.delete()


def update_user_status(user_id: str, status: str) -> AppUser:
    app_user = get_app_user(user_id)
    app_user.status = _normalize_user_status(status)
    app_user.save(update_fields=["status", "updated_at"])
    return app_user


@transaction.atomic
def set_platform_admin(user_id: str, enabled: bool) -> AppUser:
    app_user = get_app_user(user_id)
    platform_role = Role.objects.get(code=ROLE_PLATFORM_ADMIN)

    if enabled:
        UserPlatformRole.objects.get_or_create(user=app_user, role=platform_role)
        if app_user.status == AppUserStatus.PENDING:
            app_user.status = AppUserStatus.ACTIVE
            app_user.save(update_fields=["status", "updated_at"])
    else:
        UserPlatformRole.objects.filter(user=app_user, role=platform_role).delete()

    return app_user


def _membership_with_related(membership_id) -> UserOrgMembership:
    return (
        UserOrgMembership.objects.filter(id=membership_id)
        .select_related("user", "role", "org")
        .prefetch_related("facility_assignments__facility", "user__platform_role_assignments__role")
        .get()
    )


def _get_org_role(role_code: str) -> Role:
    try:
        return Role.objects.get(code=role_code, scope=RoleScope.ORG)
    except Role.DoesNotExist:
        raise ValidationError(f"Role '{role_code}' is not a valid organization role.")


def _get_membership(org: Organization, *, user_id: str, grant_id: str) -> UserOrgMembership:
    try:
        return UserOrgMembership.objects.get(id=grant_id, org=org, user_id=user_id)
    except UserOrgMembership.DoesNotExist:
        raise EntityNotFoundError(
            f"Access grant '{grant_id}' for user '{user_id}' was not found in org '{org.id}'."
        )


def _set_membership_facilities(
    membership: UserOrgMembership,
    org: Organization,
    facility_codes: list[str] | None,
) -> None:
    requested_codes = [code.strip() for code in (facility_codes or []) if code and code.strip()]
    UserMembershipFacility.objects.filter(membership=membership).delete()
    if not requested_codes:
        return

    facilities = list(Facility.objects.filter(org=org, code__in=requested_codes).order_by("code"))
    found_codes = {facility.code for facility in facilities}
    missing_codes = [code for code in requested_codes if code not in found_codes]
    if missing_codes:
        raise ValidationError(
            f"Unknown facility codes for org '{org.id}': {', '.join(missing_codes)}."
        )

    UserMembershipFacility.objects.bulk_create(
        [UserMembershipFacility(membership=membership, facility=facility) for facility in facilities]
    )


def _normalize_user_status(status: str) -> str:
    normalized = status.strip().upper()
    if normalized not in AppUserStatus.values:
        raise ValidationError(f"Unsupported user status '{status}'.")
    return normalized


def _normalize_membership_status(status: str) -> str:
    normalized = status.strip().upper()
    if normalized not in MembershipStatus.values:
        raise ValidationError(f"Unsupported membership status '{status}'.")
    return normalized
