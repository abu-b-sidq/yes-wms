from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ninja import Schema


# --- Session ---

class SessionLoginIn(Schema):
    fcm_token: str | None = None
    device_type: str = "ANDROID"  # ANDROID or IOS


class FacilityOut(Schema):
    id: str
    code: str
    name: str
    warehouse_key: str
    org_id: str


class SessionLoginOut(Schema):
    user_id: str
    email: str
    display_name: str
    photo_url: str
    last_used_facility: FacilityOut | None = None
    available_facilities: list[FacilityOut] = []


class SelectFacilityIn(Schema):
    facility_id: str


class SelectFacilityOut(Schema):
    facility: FacilityOut
    warehouse_key: str
    org_id: str


# --- Tasks ---

class PickTaskOut(Schema):
    id: str
    transaction_id: str
    transaction_type: str
    reference_number: str
    sku_code: str
    sku_name: str
    source_entity_type: str
    source_entity_code: str
    quantity: Decimal
    batch_number: str
    task_status: str
    assigned_to_name: str | None = None
    assigned_at: datetime | None = None
    task_started_at: datetime | None = None
    task_completed_at: datetime | None = None
    points_awarded: int = 0
    created_at: datetime


class DropTaskOut(Schema):
    id: str
    transaction_id: str
    transaction_type: str
    reference_number: str
    sku_code: str
    sku_name: str
    dest_entity_type: str
    dest_entity_code: str
    quantity: Decimal
    batch_number: str
    task_status: str
    assigned_to_name: str | None = None
    assigned_at: datetime | None = None
    task_started_at: datetime | None = None
    task_completed_at: datetime | None = None
    points_awarded: int = 0
    paired_pick_id: str | None = None
    created_at: datetime


class AvailableTasksOut(Schema):
    picks: list[PickTaskOut] = []
    drops: list[DropTaskOut] = []


class MyTasksOut(Schema):
    picks: list[PickTaskOut] = []
    drops: list[DropTaskOut] = []


class TaskHistoryOut(Schema):
    picks: list[PickTaskOut] = []
    drops: list[DropTaskOut] = []


class PickCompleteOut(Schema):
    pick: PickTaskOut
    drop: DropTaskOut | None = None


class DropCompleteOut(Schema):
    drop: DropTaskOut
    transaction_completed: bool = False


# --- Gamification ---

class WorkerStatsOut(Schema):
    total_points: int
    tasks_completed: int
    current_streak: int
    longest_streak: int
    last_task_completed_at: datetime | None = None
    level: str


class LeaderboardEntryOut(Schema):
    rank: int
    user_id: str
    display_name: str
    total_points: int
    tasks_completed: int
    current_streak: int


# --- Notifications ---

class RegisterDeviceIn(Schema):
    fcm_token: str
    device_type: str = "ANDROID"
