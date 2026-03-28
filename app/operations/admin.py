from django.contrib import admin

from app.operations.models import Drop, Pick, Transaction


class TimestampedAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


class PickInline(admin.TabularInline):
    model = Pick
    extra = 0
    readonly_fields = ("id", "sku", "source_entity_type", "source_entity_code", "quantity")


class DropInline(admin.TabularInline):
    model = Drop
    extra = 0
    readonly_fields = ("id", "sku", "dest_entity_type", "dest_entity_code", "quantity")


@admin.register(Transaction)
class TransactionAdmin(TimestampedAdmin):
    list_display = ("id", "org", "facility", "transaction_type", "status", "created_at")
    list_filter = ("transaction_type", "status", "org")
    list_select_related = ("org", "facility")
    search_fields = ("id", "reference_number")
    inlines = [PickInline, DropInline]


@admin.register(Pick)
class PickAdmin(TimestampedAdmin):
    list_display = ("id", "transaction", "sku", "source_entity_type", "source_entity_code", "quantity")
    list_filter = ("source_entity_type",)
    list_select_related = ("transaction", "sku", "org")
    search_fields = ("id", "transaction__reference_number", "sku__code", "source_entity_code")


@admin.register(Drop)
class DropAdmin(TimestampedAdmin):
    list_display = ("id", "transaction", "sku", "dest_entity_type", "dest_entity_code", "quantity")
    list_filter = ("dest_entity_type",)
    list_select_related = ("transaction", "sku", "org")
    search_fields = ("id", "transaction__reference_number", "sku__code", "dest_entity_code")
