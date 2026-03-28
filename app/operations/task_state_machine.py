from django.utils import timezone

from app.core.enums import TaskStatus
from app.core.exceptions import InvalidTransitionError

ALLOWED_TASK_TRANSITIONS: dict[str, list[str]] = {
    TaskStatus.PENDING: [
        TaskStatus.ASSIGNED,
        TaskStatus.CANCELLED,
    ],
    TaskStatus.ASSIGNED: [
        TaskStatus.IN_PROGRESS,
        TaskStatus.PENDING,  # unclaim / release
        TaskStatus.CANCELLED,
    ],
    TaskStatus.IN_PROGRESS: [
        TaskStatus.COMPLETED,
        TaskStatus.ASSIGNED,  # pause / return
        TaskStatus.CANCELLED,
    ],
    TaskStatus.COMPLETED: [],
    TaskStatus.CANCELLED: [],
}


def validate_task_transition(current: str, target: str) -> None:
    allowed = ALLOWED_TASK_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise InvalidTransitionError(
            f"Cannot transition task from {current} to {target}. "
            f"Allowed transitions: {allowed}"
        )


def transition_task(task, target_status: str) -> None:
    validate_task_transition(task.task_status, target_status)
    now = timezone.now()

    task.task_status = target_status

    if target_status == TaskStatus.ASSIGNED and not task.assigned_at:
        task.assigned_at = now
    elif target_status == TaskStatus.IN_PROGRESS and not task.task_started_at:
        task.task_started_at = now
    elif target_status == TaskStatus.COMPLETED:
        task.task_completed_at = now

    task.save(update_fields=[
        "task_status", "assigned_at", "task_started_at", "task_completed_at", "updated_at",
    ])
