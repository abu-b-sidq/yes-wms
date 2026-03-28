from __future__ import annotations

import logging
from datetime import timedelta

from django.db import transaction as db_transaction
from django.db.models import F, Q
from django.utils import timezone

from app.core.enums import TaskStatus, TransactionStatus
from app.core.exceptions import (
    EntityNotFoundError,
    TaskAlreadyClaimedError,
    TaskNotAssignedError,
    ValidationError,
)
from app.masters.models import AppUser, Facility, Organization
from app.operations.gamification import DailyWorkerLog, WorkerStats
from app.operations.models import Drop, Pick, Transaction
from app.operations.task_state_machine import transition_task

logger = logging.getLogger("app.operations.tasks")

LOCK_DURATION_MINUTES = 5
POINTS_PER_PICK = 10
POINTS_PER_DROP = 10
POINTS_SPEED_BONUS = 5
SPEED_BONUS_SECONDS = 120  # complete within 2 minutes for bonus


def list_available_tasks(
    org: Organization, facility: Facility
) -> list[Pick]:
    now = timezone.now()
    return list(
        Pick.objects.filter(
            org=org,
            transaction__facility=facility,
            task_status=TaskStatus.PENDING,
        )
        .filter(
            Q(locked_by__isnull=True) | Q(lock_expires_at__lt=now)
        )
        .select_related("sku", "transaction", "transaction__facility")
        .order_by("transaction__created_at")[:50]
    )


def claim_task(
    org: Organization, facility: Facility, pick_id: str, user: AppUser
) -> Pick:
    now = timezone.now()

    with db_transaction.atomic():
        try:
            pick = (
                Pick.objects.select_for_update()
                .select_related("transaction", "transaction__facility")
                .get(pk=pick_id, org=org)
            )
        except Pick.DoesNotExist:
            raise EntityNotFoundError(f"Pick task '{pick_id}' not found.")

        if pick.transaction.facility_id != facility.pk:
            raise ValidationError("Task does not belong to this facility.")

        # Check if already claimed by someone else with a valid lock
        if (
            pick.task_status == TaskStatus.ASSIGNED
            and pick.locked_by is not None
            and pick.locked_by != user
            and pick.lock_expires_at
            and pick.lock_expires_at > now
        ):
            raise TaskAlreadyClaimedError("This task has already been claimed by another worker.")

        if pick.task_status not in (TaskStatus.PENDING, TaskStatus.ASSIGNED):
            raise ValidationError(f"Cannot claim task in status '{pick.task_status}'.")

        pick.task_status = TaskStatus.ASSIGNED
        pick.assigned_to = user
        pick.assigned_at = now
        pick.locked_by = user
        pick.locked_at = now
        pick.lock_expires_at = now + timedelta(minutes=LOCK_DURATION_MINUTES)
        pick.save(update_fields=[
            "task_status", "assigned_to", "assigned_at",
            "locked_by", "locked_at", "lock_expires_at", "updated_at",
        ])

    return Pick.objects.select_related(
        "sku", "transaction", "transaction__facility", "assigned_to"
    ).get(pk=pick.pk)


def start_pick(org: Organization, pick_id: str, user: AppUser) -> Pick:
    with db_transaction.atomic():
        try:
            pick = (
                Pick.objects.select_for_update()
                .get(pk=pick_id, org=org)
            )
        except Pick.DoesNotExist:
            raise EntityNotFoundError(f"Pick task '{pick_id}' not found.")

        if pick.assigned_to != user:
            raise TaskNotAssignedError("This task is not assigned to you.")

        transition_task(pick, TaskStatus.IN_PROGRESS)
        # Extend lock while working
        now = timezone.now()
        pick.lock_expires_at = now + timedelta(minutes=LOCK_DURATION_MINUTES * 2)
        pick.save(update_fields=["lock_expires_at", "updated_at"])

    return Pick.objects.select_related(
        "sku", "transaction", "transaction__facility", "assigned_to"
    ).get(pk=pick.pk)


def complete_pick(org: Organization, pick_id: str, user: AppUser) -> tuple[Pick, Drop | None]:
    from app.inventory.services import debit_balance

    with db_transaction.atomic():
        try:
            pick = (
                Pick.objects.select_for_update()
                .select_related("sku", "transaction", "transaction__facility")
                .get(pk=pick_id, org=org)
            )
        except Pick.DoesNotExist:
            raise EntityNotFoundError(f"Pick task '{pick_id}' not found.")

        if pick.assigned_to != user:
            raise TaskNotAssignedError("This task is not assigned to you.")

        if pick.task_status != TaskStatus.IN_PROGRESS:
            raise ValidationError("Pick must be in progress to complete.")

        transition_task(pick, TaskStatus.COMPLETED)

        # Debit inventory
        debit_balance(
            org=pick.org,
            facility=pick.transaction.facility,
            sku=pick.sku,
            entity_type=pick.source_entity_type,
            entity_code=pick.source_entity_code,
            quantity=pick.quantity,
            batch_number=pick.batch_number,
            transaction=pick.transaction,
            pick=pick,
        )

        # Award points
        points = POINTS_PER_PICK
        if pick.task_started_at and (timezone.now() - pick.task_started_at).total_seconds() < SPEED_BONUS_SECONDS:
            points += POINTS_SPEED_BONUS
        pick.points_awarded = points
        pick.save(update_fields=["points_awarded", "updated_at"])

        _award_points(org, user, points)

        # Auto-assign paired drop to the same worker
        drop = None
        try:
            drop = Drop.objects.select_for_update().get(paired_pick=pick)
            drop.task_status = TaskStatus.ASSIGNED
            drop.assigned_to = user
            drop.assigned_at = timezone.now()
            drop.locked_by = user
            drop.locked_at = timezone.now()
            drop.lock_expires_at = timezone.now() + timedelta(minutes=LOCK_DURATION_MINUTES)
            drop.save(update_fields=[
                "task_status", "assigned_to", "assigned_at",
                "locked_by", "locked_at", "lock_expires_at", "updated_at",
            ])
        except Drop.DoesNotExist:
            pass

    pick = Pick.objects.select_related(
        "sku", "transaction", "transaction__facility", "assigned_to"
    ).get(pk=pick.pk)

    if drop:
        drop = Drop.objects.select_related(
            "sku", "transaction", "transaction__facility", "assigned_to", "paired_pick"
        ).get(pk=drop.pk)

    return pick, drop


def start_drop(org: Organization, drop_id: str, user: AppUser) -> Drop:
    with db_transaction.atomic():
        try:
            drop = (
                Drop.objects.select_for_update()
                .get(pk=drop_id, org=org)
            )
        except Drop.DoesNotExist:
            raise EntityNotFoundError(f"Drop task '{drop_id}' not found.")

        if drop.assigned_to != user:
            raise TaskNotAssignedError("This task is not assigned to you.")

        transition_task(drop, TaskStatus.IN_PROGRESS)
        now = timezone.now()
        drop.lock_expires_at = now + timedelta(minutes=LOCK_DURATION_MINUTES * 2)
        drop.save(update_fields=["lock_expires_at", "updated_at"])

    return Drop.objects.select_related(
        "sku", "transaction", "transaction__facility", "assigned_to", "paired_pick"
    ).get(pk=drop.pk)


def complete_drop(org: Organization, drop_id: str, user: AppUser) -> tuple[Drop, bool]:
    from app.inventory.services import credit_balance
    from app.operations.state_machine import transition

    with db_transaction.atomic():
        try:
            drop = (
                Drop.objects.select_for_update()
                .select_related("sku", "transaction", "transaction__facility")
                .get(pk=drop_id, org=org)
            )
        except Drop.DoesNotExist:
            raise EntityNotFoundError(f"Drop task '{drop_id}' not found.")

        if drop.assigned_to != user:
            raise TaskNotAssignedError("This task is not assigned to you.")

        if drop.task_status != TaskStatus.IN_PROGRESS:
            raise ValidationError("Drop must be in progress to complete.")

        transition_task(drop, TaskStatus.COMPLETED)

        # Credit inventory
        credit_balance(
            org=drop.org,
            facility=drop.transaction.facility,
            sku=drop.sku,
            entity_type=drop.dest_entity_type,
            entity_code=drop.dest_entity_code,
            quantity=drop.quantity,
            batch_number=drop.batch_number,
            transaction=drop.transaction,
            drop=drop,
        )

        # Award points
        points = POINTS_PER_DROP
        if drop.task_started_at and (timezone.now() - drop.task_started_at).total_seconds() < SPEED_BONUS_SECONDS:
            points += POINTS_SPEED_BONUS
        drop.points_awarded = points
        drop.save(update_fields=["points_awarded", "updated_at"])

        _award_points(org, user, points)

        # Check if all picks and drops for this transaction are completed
        txn = drop.transaction
        transaction_completed = False
        all_picks_done = not txn.picks.exclude(task_status=TaskStatus.COMPLETED).exists()
        all_drops_done = not txn.drops.exclude(task_status=TaskStatus.COMPLETED).exists()

        if all_picks_done and all_drops_done:
            if txn.status == TransactionStatus.PENDING:
                transition(txn, TransactionStatus.IN_PROGRESS)
            transition(txn, TransactionStatus.COMPLETED)
            transaction_completed = True

            # Generate document if configured
            from app.documents.services import generate_and_store_document
            url = generate_and_store_document(txn)
            if url:
                txn.document_url = url
                txn.save(update_fields=["document_url", "updated_at"])

    drop = Drop.objects.select_related(
        "sku", "transaction", "transaction__facility", "assigned_to", "paired_pick"
    ).get(pk=drop.pk)

    return drop, transaction_completed


def get_my_tasks(
    org: Organization, facility: Facility, user: AppUser
) -> dict:
    active_picks = list(
        Pick.objects.filter(
            org=org,
            transaction__facility=facility,
            assigned_to=user,
            task_status__in=[TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS],
        )
        .select_related("sku", "transaction", "transaction__facility")
        .order_by("-assigned_at")
    )
    active_drops = list(
        Drop.objects.filter(
            org=org,
            transaction__facility=facility,
            assigned_to=user,
            task_status__in=[TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS],
        )
        .select_related("sku", "transaction", "transaction__facility", "paired_pick")
        .order_by("-assigned_at")
    )
    return {"picks": active_picks, "drops": active_drops}


def get_task_history(
    org: Organization, facility: Facility, user: AppUser, limit: int = 50
) -> dict:
    completed_picks = list(
        Pick.objects.filter(
            org=org,
            transaction__facility=facility,
            assigned_to=user,
            task_status=TaskStatus.COMPLETED,
        )
        .select_related("sku", "transaction")
        .order_by("-task_completed_at")[:limit]
    )
    completed_drops = list(
        Drop.objects.filter(
            org=org,
            transaction__facility=facility,
            assigned_to=user,
            task_status=TaskStatus.COMPLETED,
        )
        .select_related("sku", "transaction")
        .order_by("-task_completed_at")[:limit]
    )
    return {"picks": completed_picks, "drops": completed_drops}


def get_leaderboard(org: Organization, facility: Facility, limit: int = 20) -> list[dict]:
    stats = (
        WorkerStats.objects.filter(org=org)
        .filter(
            Q(user__assigned_picks__transaction__facility=facility)
            | Q(user__assigned_drops__transaction__facility=facility)
        )
        .select_related("user")
        .distinct()
        .order_by("-total_points")[:limit]
    )
    result = []
    for i, s in enumerate(stats, 1):
        result.append({
            "rank": i,
            "user_id": str(s.user_id),
            "display_name": s.user.display_name or s.user.email,
            "total_points": s.total_points,
            "tasks_completed": s.tasks_completed,
            "current_streak": s.current_streak,
        })
    return result


def get_worker_stats(org: Organization, user: AppUser) -> dict:
    stats, _ = WorkerStats.objects.get_or_create(
        org=org, user=user,
        defaults={"created_by": str(user.pk), "updated_by": str(user.pk)},
    )
    return {
        "total_points": stats.total_points,
        "tasks_completed": stats.tasks_completed,
        "current_streak": stats.current_streak,
        "longest_streak": stats.longest_streak,
        "last_task_completed_at": stats.last_task_completed_at,
        "level": _get_level(stats.total_points),
    }


def release_expired_locks() -> int:
    now = timezone.now()
    count = 0
    for Model in (Pick, Drop):
        expired = Model.objects.filter(
            task_status=TaskStatus.ASSIGNED,
            lock_expires_at__lt=now,
        )
        count += expired.update(
            task_status=TaskStatus.PENDING,
            assigned_to=None,
            assigned_at=None,
            locked_by=None,
            locked_at=None,
            lock_expires_at=None,
        )
    return count


# --- Internal helpers ---

def _award_points(org: Organization, user: AppUser, points: int) -> None:
    now = timezone.now()
    today = now.date()

    stats, created = WorkerStats.objects.get_or_create(
        org=org, user=user,
        defaults={
            "created_by": str(user.pk),
            "updated_by": str(user.pk),
            "total_points": points,
            "tasks_completed": 1,
            "current_streak": 1,
            "longest_streak": 1,
            "last_task_completed_at": now,
        },
    )
    if not created:
        stats.total_points = F("total_points") + points
        stats.tasks_completed = F("tasks_completed") + 1

        # Update streak
        if stats.last_task_completed_at:
            last_date = stats.last_task_completed_at.date()
            if last_date == today:
                pass  # same day, no streak change
            elif last_date == today - timedelta(days=1):
                stats.current_streak = F("current_streak") + 1
            else:
                stats.current_streak = 1
        else:
            stats.current_streak = 1

        stats.last_task_completed_at = now
        stats.save(update_fields=[
            "total_points", "tasks_completed", "current_streak",
            "last_task_completed_at", "updated_at",
        ])

        # Refresh to get actual values for longest_streak comparison
        stats.refresh_from_db()
        if stats.current_streak > stats.longest_streak:
            stats.longest_streak = stats.current_streak
            stats.save(update_fields=["longest_streak", "updated_at"])

    # Update daily log
    daily_log, created = DailyWorkerLog.objects.get_or_create(
        user=user, org=org, date=today,
        defaults={"tasks_completed": 1, "points_earned": points},
    )
    if not created:
        daily_log.tasks_completed = F("tasks_completed") + 1
        daily_log.points_earned = F("points_earned") + points
        daily_log.save(update_fields=["tasks_completed", "points_earned", "updated_at"])


def _get_level(total_points: int) -> str:
    if total_points >= 5000:
        return "MASTER"
    elif total_points >= 2000:
        return "EXPERT"
    elif total_points >= 500:
        return "PRO"
    return "ROOKIE"
