from django.db import models

from app.core.base_models import TenantAwareModel
from app.core.enums import EntityType, TaskStatus, TransactionStatus, TransactionType


class Transaction(TenantAwareModel):
    facility = models.ForeignKey(
        "app_masters.Facility",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=20, choices=TransactionType.choices
    )
    status = models.CharField(
        max_length=25,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
    )
    reference_number = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    document_url = models.URLField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "app_transaction"
        indexes = [
            models.Index(
                fields=["org", "facility", "transaction_type", "status"],
                name="idx_txn_org_fac_type_status",
            ),
            models.Index(
                fields=["org", "reference_number"],
                name="idx_txn_org_ref",
            ),
        ]

    def __str__(self):
        return f"{self.transaction_type}:{self.id}({self.status})"


class Pick(TenantAwareModel):
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="picks"
    )
    sku = models.ForeignKey(
        "app_masters.SKU", on_delete=models.CASCADE, related_name="picks"
    )
    source_entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    source_entity_code = models.CharField(max_length=100)
    source_location = models.ForeignKey(
        "app_masters.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="picks",
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    batch_number = models.CharField(max_length=100, blank=True, default="")

    task_status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )
    assigned_to = models.ForeignKey(
        "app_masters.AppUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_picks",
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    task_started_at = models.DateTimeField(null=True, blank=True)
    task_completed_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        "app_masters.AppUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locked_picks",
    )
    locked_at = models.DateTimeField(null=True, blank=True)
    lock_expires_at = models.DateTimeField(null=True, blank=True)
    points_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "app_pick"
        indexes = [
            models.Index(
                fields=["transaction"],
                name="idx_pick_txn",
            ),
            models.Index(
                fields=["org", "task_status"],
                name="idx_pick_org_task_status",
            ),
        ]

    def __str__(self):
        return f"Pick({self.sku_id} x {self.quantity} from {self.source_entity_type}:{self.source_entity_code})"


class Drop(TenantAwareModel):
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="drops"
    )
    sku = models.ForeignKey(
        "app_masters.SKU", on_delete=models.CASCADE, related_name="drops"
    )
    dest_entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    dest_entity_code = models.CharField(max_length=100)
    dest_location = models.ForeignKey(
        "app_masters.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drops",
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    batch_number = models.CharField(max_length=100, blank=True, default="")
    paired_pick = models.OneToOneField(
        Pick,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paired_drop",
    )

    task_status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )
    assigned_to = models.ForeignKey(
        "app_masters.AppUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_drops",
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    task_started_at = models.DateTimeField(null=True, blank=True)
    task_completed_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        "app_masters.AppUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locked_drops",
    )
    locked_at = models.DateTimeField(null=True, blank=True)
    lock_expires_at = models.DateTimeField(null=True, blank=True)
    points_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "app_drop"
        indexes = [
            models.Index(
                fields=["transaction"],
                name="idx_drop_txn",
            ),
            models.Index(
                fields=["org", "task_status"],
                name="idx_drop_org_task_status",
            ),
        ]

    def __str__(self):
        return f"Drop({self.sku_id} x {self.quantity} to {self.dest_entity_type}:{self.dest_entity_code})"
