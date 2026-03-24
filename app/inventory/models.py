from django.db import models

from app.core.base_models import TenantAwareModel
from app.core.enums import EntityType, LedgerEntryType


class InventoryBalance(TenantAwareModel):
    facility = models.ForeignKey(
        "app_masters.Facility",
        on_delete=models.CASCADE,
        related_name="inventory_balances",
    )
    sku = models.ForeignKey(
        "app_masters.SKU",
        on_delete=models.CASCADE,
        related_name="inventory_balances",
    )
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    entity_code = models.CharField(max_length=100)
    batch_number = models.CharField(max_length=100, blank=True, default="")
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    quantity_reserved = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    quantity_available = models.DecimalField(max_digits=12, decimal_places=4, default=0)

    class Meta:
        db_table = "app_inventory_balance"
        constraints = [
            models.UniqueConstraint(
                fields=["org", "facility", "sku", "entity_type", "entity_code", "batch_number"],
                name="uq_inv_balance",
            ),
        ]
        indexes = [
            models.Index(
                fields=["org", "facility", "sku"],
                name="idx_inv_bal_org_fac_sku",
            ),
            models.Index(
                fields=["org", "facility", "entity_type", "entity_code"],
                name="idx_inv_bal_entity",
            ),
        ]

    def __str__(self):
        return (
            f"Balance({self.sku_id} @ {self.entity_type}:{self.entity_code} "
            f"= {self.quantity_on_hand})"
        )


class InventoryLedger(TenantAwareModel):
    facility = models.ForeignKey(
        "app_masters.Facility",
        on_delete=models.CASCADE,
        related_name="inventory_ledger_entries",
    )
    sku = models.ForeignKey(
        "app_masters.SKU",
        on_delete=models.CASCADE,
        related_name="inventory_ledger_entries",
    )
    transaction = models.ForeignKey(
        "app_operations.Transaction",
        on_delete=models.CASCADE,
        related_name="ledger_entries",
    )
    entry_type = models.CharField(max_length=10, choices=LedgerEntryType.choices)
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    entity_code = models.CharField(max_length=100)
    batch_number = models.CharField(max_length=100, blank=True, default="")
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    balance_after = models.DecimalField(max_digits=12, decimal_places=4)
    pick = models.ForeignKey(
        "app_operations.Pick",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entries",
    )
    drop = models.ForeignKey(
        "app_operations.Drop",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entries",
    )

    class Meta:
        db_table = "app_inventory_ledger"
        indexes = [
            models.Index(
                fields=["org", "facility", "sku", "created_at"],
                name="idx_ledger_org_fac_sku_date",
            ),
            models.Index(
                fields=["transaction"],
                name="idx_ledger_txn",
            ),
        ]

    def __str__(self):
        return (
            f"Ledger({self.entry_type} {self.quantity} "
            f"{self.sku_id} @ {self.entity_type}:{self.entity_code})"
        )
