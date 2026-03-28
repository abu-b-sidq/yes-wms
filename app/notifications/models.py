from django.db import models

from app.core.base_models import UUIDPrimaryKeyMixin, TimestampedModel


class DeviceToken(UUIDPrimaryKeyMixin, TimestampedModel):
    user = models.ForeignKey(
        "app_masters.AppUser",
        on_delete=models.CASCADE,
        related_name="device_tokens",
    )
    token = models.CharField(max_length=500)
    device_type = models.CharField(
        max_length=10,
        choices=[("ANDROID", "Android"), ("IOS", "iOS")],
    )
    is_active = models.BooleanField(default=True)
    facility = models.ForeignKey(
        "app_masters.Facility",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="device_tokens",
    )

    class Meta:
        db_table = "app_device_token"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "token"],
                name="uq_device_token_user_token",
            ),
        ]

    def __str__(self):
        return f"DeviceToken({self.user_id}, {self.device_type})"
