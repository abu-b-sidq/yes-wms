from __future__ import annotations

from ninja import Router

from app.auth.authorization import authorize_request
from app.auth.permissions import PERM_OPERATIONS_EXECUTE
from app.core.context import get_auth_context
from app.core.exceptions import AuthorizationError, EntityNotFoundError, ValidationError
from app.core.openapi import protected_openapi_extra
from app.core.response import success_response
from app.core.tenant import resolve_request_tenant
from app.masters.models import (
    AppUser,
    Facility,
    MembershipStatus,
    UserMembershipFacility,
    UserOrgMembership,
)
from app.notifications.models import DeviceToken
from app.operations import mobile_schemas as schemas
from app.operations import task_service

router = Router(tags=["mobile"])

ORG_PROTECTED = protected_openapi_extra()
ORG_WITH_REQUIRED_FACILITY = protected_openapi_extra(require_facility=True)


# ---------------------------------------------------------------------------
# Session / Login
# ---------------------------------------------------------------------------

@router.post(
    "/session/login",
    summary="Mobile login",
    description=(
        "Called after Firebase auth on mobile. Registers FCM token and returns "
        "user profile with available facilities and last used warehouse."
    ),
    openapi_extra=ORG_PROTECTED,
)
def session_login(request, payload: schemas.SessionLoginIn):
    authorize_request(request, require_firebase=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)

    # Register FCM token if provided
    if payload.fcm_token:
        DeviceToken.objects.update_or_create(
            user=user,
            token=payload.fcm_token,
            defaults={
                "device_type": payload.device_type,
                "is_active": True,
            },
        )

    # Get available facilities from user's org memberships
    available_facilities = _get_user_facilities(user)

    # Last used facility
    last_facility_out = None
    if user.last_facility:
        last_facility_out = schemas.FacilityOut(
            id=str(user.last_facility.pk),
            code=user.last_facility.code,
            name=user.last_facility.name,
            warehouse_key=user.last_facility.warehouse_key,
            org_id=str(user.last_facility.org_id),
        )

    return success_response(request, data=schemas.SessionLoginOut(
        user_id=str(user.pk),
        email=user.email,
        display_name=user.display_name,
        photo_url=user.photo_url,
        last_used_facility=last_facility_out,
        available_facilities=available_facilities,
    ).dict())


@router.post(
    "/session/select-facility",
    summary="Select active facility",
    description="Sets the user's active facility for this session.",
    openapi_extra=ORG_PROTECTED,
)
def session_select_facility(request, payload: schemas.SelectFacilityIn):
    authorize_request(request, require_firebase=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)

    try:
        facility = Facility.objects.get(pk=payload.facility_id)
    except Facility.DoesNotExist:
        raise EntityNotFoundError(f"Facility '{payload.facility_id}' not found.")

    # Verify user has access to this facility
    user_facilities = _get_user_facilities(user)
    if not any(f.id == str(facility.pk) for f in user_facilities):
        raise AuthorizationError("You do not have access to this facility.")

    # Update last_facility
    user.last_facility = facility
    user.save(update_fields=["last_facility", "updated_at"])

    return success_response(request, data=schemas.SelectFacilityOut(
        facility=schemas.FacilityOut(
            id=str(facility.pk),
            code=facility.code,
            name=facility.name,
            warehouse_key=facility.warehouse_key,
            org_id=str(facility.org_id),
        ),
        warehouse_key=facility.warehouse_key,
        org_id=str(facility.org_id),
    ).dict())


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@router.get(
    "/tasks/available",
    summary="List available tasks",
    description="Returns unclaimed pick and drop tasks for the worker's current facility.",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def list_available_tasks(request):
    authorize_request(request, PERM_OPERATIONS_EXECUTE, require_membership=True)
    org, facility = resolve_request_tenant(request, require_facility=True)
    tasks = task_service.list_available_tasks(org, facility)
    return success_response(request, data=schemas.AvailableTasksOut(
        picks=[_pick_task_out(p) for p in tasks["picks"]],
        drops=[_drop_task_out(d) for d in tasks["drops"]],
    ).dict())


@router.post(
    "/tasks/picks/{pick_id}/claim",
    summary="Claim a pick task",
    description="Lock and assign a pick task to the current worker.",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def claim_pick_task(request, pick_id: str):
    authorize_request(request, PERM_OPERATIONS_EXECUTE, require_membership=True)
    org, facility = resolve_request_tenant(request, require_facility=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)
    pick = task_service.claim_task(org, facility, pick_id, user)

    # Notify via WebSocket that task was claimed
    _notify_task_claimed(facility, "pick", pick)

    return success_response(request, data=_pick_task_out(pick))


@router.post(
    "/tasks/drops/{drop_id}/claim",
    summary="Claim a drop task",
    description="Lock and assign a drop task to the current worker.",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def claim_drop_task(request, drop_id: str):
    authorize_request(request, PERM_OPERATIONS_EXECUTE, require_membership=True)
    org, facility = resolve_request_tenant(request, require_facility=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)
    drop = task_service.claim_drop(org, facility, drop_id, user)

    _notify_task_claimed(facility, "drop", drop)

    return success_response(request, data=_drop_task_out(drop))


@router.post(
    "/tasks/picks/{pick_id}/start",
    summary="Start a pick task",
    description="Mark an assigned pick task as in-progress.",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def start_pick_task(request, pick_id: str):
    authorize_request(request, PERM_OPERATIONS_EXECUTE, require_membership=True)
    org, _ = resolve_request_tenant(request, require_facility=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)
    pick = task_service.start_pick(org, pick_id, user)
    return success_response(request, data=_pick_task_out(pick))


@router.post(
    "/tasks/picks/{pick_id}/complete",
    summary="Complete a pick task",
    description="Complete pick, debit inventory, auto-assign paired drop to same worker.",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def complete_pick_task(request, pick_id: str):
    authorize_request(request, PERM_OPERATIONS_EXECUTE, require_membership=True)
    org, facility = resolve_request_tenant(request, require_facility=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)
    pick, drop = task_service.complete_pick(org, pick_id, user)

    result = schemas.PickCompleteOut(
        pick=_pick_task_out(pick),
        drop=_drop_task_out(drop) if drop else None,
    ).dict()

    # Notify via WebSocket/push
    if drop:
        _notify_drop_assigned(user, drop)

    return success_response(request, data=result)


@router.post(
    "/tasks/drops/{drop_id}/start",
    summary="Start a drop task",
    description="Mark an assigned drop task as in-progress.",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def start_drop_task(request, drop_id: str):
    authorize_request(request, PERM_OPERATIONS_EXECUTE, require_membership=True)
    org, _ = resolve_request_tenant(request, require_facility=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)
    drop = task_service.start_drop(org, drop_id, user)
    return success_response(request, data=_drop_task_out(drop))


@router.post(
    "/tasks/drops/{drop_id}/complete",
    summary="Complete a drop task",
    description="Complete drop, credit inventory. If all tasks done, transaction completes.",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def complete_drop_task(request, drop_id: str):
    authorize_request(request, PERM_OPERATIONS_EXECUTE, require_membership=True)
    org, facility = resolve_request_tenant(request, require_facility=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)
    drop, transaction_completed = task_service.complete_drop(org, drop_id, user)

    result = schemas.DropCompleteOut(
        drop=_drop_task_out(drop),
        transaction_completed=transaction_completed,
    ).dict()

    if transaction_completed:
        _notify_transaction_completed(facility, drop.transaction)

    return success_response(request, data=result)


@router.get(
    "/tasks/my",
    summary="My active tasks",
    description="Returns pick and drop tasks currently assigned to the worker.",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def my_tasks(request):
    authorize_request(request, PERM_OPERATIONS_EXECUTE, require_membership=True)
    org, facility = resolve_request_tenant(request, require_facility=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)
    tasks = task_service.get_my_tasks(org, facility, user)
    return success_response(request, data=schemas.MyTasksOut(
        picks=[_pick_task_out(p) for p in tasks["picks"]],
        drops=[_drop_task_out(d) for d in tasks["drops"]],
    ).dict())


@router.get(
    "/tasks/history",
    summary="Task history",
    description="Returns completed tasks for the worker.",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def task_history(request):
    authorize_request(request, PERM_OPERATIONS_EXECUTE, require_membership=True)
    org, facility = resolve_request_tenant(request, require_facility=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)
    history = task_service.get_task_history(org, facility, user)
    return success_response(request, data=schemas.TaskHistoryOut(
        picks=[_pick_task_out(p) for p in history["picks"]],
        drops=[_drop_task_out(d) for d in history["drops"]],
    ).dict())


# ---------------------------------------------------------------------------
# Gamification
# ---------------------------------------------------------------------------

@router.get(
    "/gamification/stats",
    summary="Worker stats",
    description="Returns the current worker's points, streak, and level.",
    openapi_extra=ORG_PROTECTED,
)
def worker_stats(request):
    authorize_request(request, require_firebase=True, require_membership=True)
    org, _ = resolve_request_tenant(request)
    auth = get_auth_context(request)
    user = _get_app_user(auth)
    stats = task_service.get_worker_stats(org, user)
    return success_response(request, data=stats)


@router.get(
    "/gamification/leaderboard",
    summary="Facility leaderboard",
    description="Returns top workers by points for the current facility.",
    openapi_extra=ORG_WITH_REQUIRED_FACILITY,
)
def leaderboard(request):
    authorize_request(request, require_firebase=True, require_membership=True)
    org, facility = resolve_request_tenant(request, require_facility=True)
    entries = task_service.get_leaderboard(org, facility)
    return success_response(request, data=entries)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@router.post(
    "/notifications/register-device",
    summary="Register FCM device token",
    description="Register or update a device token for push notifications.",
    openapi_extra=ORG_PROTECTED,
)
def register_device(request, payload: schemas.RegisterDeviceIn):
    authorize_request(request, require_firebase=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)

    facility = None
    facility_code = request.headers.get("X-Facility-Id", "").strip()
    if facility_code:
        org_id = request.headers.get("X-Org-Id", "").strip()
        if org_id:
            facility = Facility.objects.filter(org_id=org_id, code=facility_code).first()

    DeviceToken.objects.update_or_create(
        user=user,
        token=payload.fcm_token,
        defaults={
            "device_type": payload.device_type,
            "is_active": True,
            "facility": facility,
        },
    )
    return success_response(request, data={"registered": True})


@router.delete(
    "/notifications/register-device",
    summary="Unregister FCM device token",
    description="Deactivate a device token.",
    openapi_extra=ORG_PROTECTED,
)
def unregister_device(request, payload: schemas.RegisterDeviceIn):
    authorize_request(request, require_firebase=True)
    auth = get_auth_context(request)
    user = _get_app_user(auth)
    DeviceToken.objects.filter(user=user, token=payload.fcm_token).update(is_active=False)
    return success_response(request, data={"unregistered": True})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_app_user(auth) -> AppUser:
    if not auth.app_user_id:
        raise AuthorizationError("Firebase authentication required.")
    try:
        return AppUser.objects.get(pk=auth.app_user_id)
    except AppUser.DoesNotExist:
        raise EntityNotFoundError("User not found.")


def _get_user_facilities(user: AppUser) -> list[schemas.FacilityOut]:
    memberships = UserOrgMembership.objects.filter(
        user=user,
        status=MembershipStatus.ACTIVE,
    )
    facility_ids = set()
    for m in memberships:
        for fa in m.facility_assignments.select_related("facility").all():
            facility_ids.add(fa.facility_id)

    facilities = Facility.objects.filter(pk__in=facility_ids, is_active=True)
    return [
        schemas.FacilityOut(
            id=str(f.pk),
            code=f.code,
            name=f.name,
            warehouse_key=f.warehouse_key,
            org_id=str(f.org_id),
        )
        for f in facilities
    ]


def _pick_task_out(pick) -> schemas.PickTaskOut:
    return schemas.PickTaskOut(
        id=str(pick.pk),
        transaction_id=str(pick.transaction_id),
        transaction_type=pick.transaction.transaction_type,
        reference_number=pick.transaction.reference_number,
        sku_code=pick.sku.code,
        sku_name=pick.sku.name,
        source_entity_type=pick.source_entity_type,
        source_entity_code=pick.source_entity_code,
        quantity=pick.quantity,
        batch_number=pick.batch_number,
        task_status=pick.task_status,
        assigned_to_name=(
            pick.assigned_to.display_name or pick.assigned_to.email
            if pick.assigned_to else None
        ),
        assigned_at=pick.assigned_at,
        task_started_at=pick.task_started_at,
        task_completed_at=pick.task_completed_at,
        points_awarded=pick.points_awarded,
        created_at=pick.created_at,
    )


def _drop_task_out(drop) -> schemas.DropTaskOut:
    return schemas.DropTaskOut(
        id=str(drop.pk),
        transaction_id=str(drop.transaction_id),
        transaction_type=drop.transaction.transaction_type,
        reference_number=drop.transaction.reference_number,
        sku_code=drop.sku.code,
        sku_name=drop.sku.name,
        dest_entity_type=drop.dest_entity_type,
        dest_entity_code=drop.dest_entity_code,
        quantity=drop.quantity,
        batch_number=drop.batch_number,
        task_status=drop.task_status,
        assigned_to_name=(
            drop.assigned_to.display_name or drop.assigned_to.email
            if drop.assigned_to else None
        ),
        assigned_at=drop.assigned_at,
        task_started_at=drop.task_started_at,
        task_completed_at=drop.task_completed_at,
        points_awarded=drop.points_awarded,
        paired_pick_id=str(drop.paired_pick_id) if drop.paired_pick_id else None,
        created_at=drop.created_at,
    )


def _notify_task_claimed(facility, task_type: str, task):
    """Send WebSocket notification that a task was claimed."""
    try:
        from app.notifications.websocket import broadcast_to_facility
        broadcast_to_facility(str(facility.pk), {
            "type": "task_claimed",
            "task_type": task_type,
            "task_id": str(task.pk),
            "claimed_by": task.assigned_to.display_name if task.assigned_to else "",
        })
    except Exception:
        pass  # Non-critical, don't fail the request


def _notify_drop_assigned(user, drop):
    """Send push notification + WebSocket for drop assignment."""
    try:
        from app.notifications.fcm_service import notify_drop_assigned
        notify_drop_assigned(user, drop)
    except Exception:
        pass

    try:
        from app.notifications.websocket import send_to_user
        send_to_user(str(user.pk), {
            "type": "drop_assigned",
            "drop_id": str(drop.pk),
            "sku_code": drop.sku.code,
            "dest_entity_code": drop.dest_entity_code,
        })
    except Exception:
        pass


def _notify_transaction_completed(facility, transaction):
    """Send WebSocket notification that a transaction was completed."""
    try:
        from app.notifications.websocket import broadcast_to_facility
        broadcast_to_facility(str(facility.pk), {
            "type": "transaction_completed",
            "transaction_id": str(transaction.pk),
        })
    except Exception:
        pass
