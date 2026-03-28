from django.db import models

from app.core.base_models import TenantAwareModel, TimestampedModel, UUIDPrimaryKeyMixin


class WorkerStats(TenantAwareModel):
    user = models.ForeignKey(
        "app_masters.AppUser",
        on_delete=models.CASCADE,
        related_name="worker_stats",
    )
    total_points = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_task_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "app_worker_stats"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "org"],
                name="uq_worker_stats_user_org",
            ),
        ]

    def __str__(self):
        return f"WorkerStats({self.user_id}, pts={self.total_points})"


class DailyWorkerLog(UUIDPrimaryKeyMixin, TimestampedModel):
    user = models.ForeignKey(
        "app_masters.AppUser",
        on_delete=models.CASCADE,
        related_name="daily_logs",
    )
    org = models.ForeignKey(
        "app_masters.Organization",
        on_delete=models.CASCADE,
        related_name="daily_worker_logs",
    )
    date = models.DateField()
    tasks_completed = models.IntegerField(default=0)
    points_earned = models.IntegerField(default=0)

    class Meta:
        db_table = "app_daily_worker_log"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "org", "date"],
                name="uq_daily_log_user_org_date",
            ),
        ]

    def __str__(self):
        return f"DailyLog({self.user_id}, {self.date}, pts={self.points_earned})"
