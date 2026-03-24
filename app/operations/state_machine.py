from django.utils import timezone

from app.core.enums import TransactionStatus
from app.core.exceptions import InvalidTransitionError

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    TransactionStatus.PENDING: [
        TransactionStatus.IN_PROGRESS,
        TransactionStatus.CANCELLED,
    ],
    TransactionStatus.IN_PROGRESS: [
        TransactionStatus.COMPLETED,
        TransactionStatus.FAILED,
        TransactionStatus.CANCELLED,
        TransactionStatus.PARTIALLY_COMPLETED,
    ],
    TransactionStatus.PARTIALLY_COMPLETED: [
        TransactionStatus.IN_PROGRESS,
        TransactionStatus.COMPLETED,
        TransactionStatus.CANCELLED,
    ],
    TransactionStatus.COMPLETED: [],
    TransactionStatus.FAILED: [
        TransactionStatus.PENDING,
    ],
    TransactionStatus.CANCELLED: [],
}


def validate_transition(current: str, target: str) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise InvalidTransitionError(
            f"Cannot transition from {current} to {target}. "
            f"Allowed transitions: {allowed}"
        )


def transition(transaction, target_status: str) -> None:
    validate_transition(transaction.status, target_status)
    now = timezone.now()

    transaction.status = target_status

    if target_status == TransactionStatus.IN_PROGRESS and not transaction.started_at:
        transaction.started_at = now
    elif target_status == TransactionStatus.COMPLETED:
        transaction.completed_at = now
    elif target_status == TransactionStatus.CANCELLED:
        transaction.cancelled_at = now

    transaction.save(update_fields=["status", "started_at", "completed_at", "cancelled_at", "updated_at"])
