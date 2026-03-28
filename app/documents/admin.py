from django.contrib import admin

from app.documents.models import TransactionDocumentConfig


@admin.register(TransactionDocumentConfig)
class TransactionDocumentConfigAdmin(admin.ModelAdmin):
    list_display = (
        "org",
        "facility",
        "transaction_type",
        "is_enabled",
        "template_name",
        "created_at",
    )
    list_filter = ("is_enabled", "transaction_type", "org")
    list_select_related = ("org", "facility")
    search_fields = ("org__id", "org__name", "facility__code", "template_name")
    autocomplete_fields = ("org", "facility")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
