from django.contrib import admin

from app.operations.models import Drop, Pick, Transaction


class PickInline(admin.TabularInline):
    model = Pick
    extra = 0
    readonly_fields = ("id", "sku", "source_entity_type", "source_entity_code", "quantity")


class DropInline(admin.TabularInline):
    model = Drop
    extra = 0
    readonly_fields = ("id", "sku", "dest_entity_type", "dest_entity_code", "quantity")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "org", "facility", "transaction_type", "status", "created_at")
    list_filter = ("transaction_type", "status", "org")
    search_fields = ("id", "reference_number")
    inlines = [PickInline, DropInline]


@admin.register(Pick)
class PickAdmin(admin.ModelAdmin):
    list_display = ("id", "transaction", "sku", "source_entity_type", "source_entity_code", "quantity")
    list_filter = ("source_entity_type",)


@admin.register(Drop)
class DropAdmin(admin.ModelAdmin):
    list_display = ("id", "transaction", "sku", "dest_entity_type", "dest_entity_code", "quantity")
    list_filter = ("dest_entity_type",)
