import pytest

from app.core.enums import TransactionStatus
from app.core.exceptions import InvalidTransitionError
from app.operations.state_machine import validate_transition


class TestStateMachine:
    def test_pending_to_in_progress(self):
        validate_transition(TransactionStatus.PENDING, TransactionStatus.IN_PROGRESS)

    def test_pending_to_cancelled(self):
        validate_transition(TransactionStatus.PENDING, TransactionStatus.CANCELLED)

    def test_in_progress_to_completed(self):
        validate_transition(TransactionStatus.IN_PROGRESS, TransactionStatus.COMPLETED)

    def test_in_progress_to_failed(self):
        validate_transition(TransactionStatus.IN_PROGRESS, TransactionStatus.FAILED)

    def test_in_progress_to_cancelled(self):
        validate_transition(TransactionStatus.IN_PROGRESS, TransactionStatus.CANCELLED)

    def test_in_progress_to_partially_completed(self):
        validate_transition(
            TransactionStatus.IN_PROGRESS, TransactionStatus.PARTIALLY_COMPLETED
        )

    def test_partially_completed_to_completed(self):
        validate_transition(
            TransactionStatus.PARTIALLY_COMPLETED, TransactionStatus.COMPLETED
        )

    def test_failed_to_pending(self):
        validate_transition(TransactionStatus.FAILED, TransactionStatus.PENDING)

    def test_completed_cannot_transition(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(
                TransactionStatus.COMPLETED, TransactionStatus.IN_PROGRESS
            )

    def test_cancelled_cannot_transition(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(
                TransactionStatus.CANCELLED, TransactionStatus.PENDING
            )

    def test_pending_to_completed_not_allowed(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(
                TransactionStatus.PENDING, TransactionStatus.COMPLETED
            )

    def test_pending_to_failed_not_allowed(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(TransactionStatus.PENDING, TransactionStatus.FAILED)
