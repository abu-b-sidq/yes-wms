from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from app.auth.permissions import ROLE_PLATFORM_ADMIN
from app.core.config import get_runtime_settings
from app.masters.models import AppUser, AppUserStatus, Role, UserPlatformRole


def _claim_value(claims: dict, *keys: str) -> str:
    for key in keys:
        value = claims.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _normalize_email(value: str) -> str:
    return value.strip().lower()


@transaction.atomic
def sync_firebase_user(claims: dict) -> AppUser:
    firebase_uid = _claim_value(claims, "uid", "sub")
    if not firebase_uid:
        raise ValueError("Firebase claims must include `uid` or `sub`.")

    settings = get_runtime_settings()
    email = _normalize_email(_claim_value(claims, "email"))
    display_name = _claim_value(claims, "name", "display_name")
    phone_number = _claim_value(claims, "phone_number")
    photo_url = _claim_value(claims, "picture")

    user, _ = AppUser.objects.get_or_create(
        firebase_uid=firebase_uid,
        defaults={
            "email": email,
            "display_name": display_name,
            "phone_number": phone_number,
            "photo_url": photo_url,
            "status": AppUserStatus.PENDING,
            "last_login_at": timezone.now(),
        },
    )

    user.email = email
    user.display_name = display_name
    user.phone_number = phone_number
    user.photo_url = photo_url
    user.last_login_at = timezone.now()

    if firebase_uid in settings.bootstrap_platform_admin_uids:
        user.status = AppUserStatus.ACTIVE

    user.save(
        update_fields=[
            "email",
            "display_name",
            "phone_number",
            "photo_url",
            "status",
            "last_login_at",
            "updated_at",
        ]
    )

    if firebase_uid in settings.bootstrap_platform_admin_uids:
        platform_role = Role.objects.get(code=ROLE_PLATFORM_ADMIN)
        UserPlatformRole.objects.get_or_create(user=user, role=platform_role)

    return user

