from django.contrib import admin

from app.inventory.models import InventoryBalance, InventoryLedger


@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "sku", "facility", "entity_type", "entity_code",
        "quantity_on_hand", "quantity_reserved", "quantity_available",
    )
    list_filter = ("entity_type", "org", "facility")
    search_fields = ("sku__code", "entity_code")


@admin.register(InventoryLedger)
class InventoryLedgerAdmin(admin.ModelAdmin):
    list_display = (
        "entry_type", "sku", "entity_type", "entity_code",
        "quantity", "balance_after", "transaction", "created_at",
    )
    list_filter = ("entry_type", "entity_type", "org")
    search_fields = ("sku__code", "entity_code")
    readonly_fields = ("id", "org", "facility", "sku", "transaction", "entry_type",
                       "entity_type", "entity_code", "quantity", "balance_after",
                       "pick", "drop")
