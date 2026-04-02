from __future__ import annotations

import json

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils import timezone

from app.connectors import services
from app.connectors.enums import SyncStatus
from app.connectors.models import ConnectorConfig, ExternalEntityMapping, SyncLog


def _format_json(value) -> str:
    if not value:
        return "-"
    return format_html(
        "<pre>{}</pre>",
        json.dumps(value, indent=2, sort_keys=True, default=str),
    )


class TimestampedAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


class ReadOnlyAdminMixin:
    actions = None

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_view_permission(self, request: HttpRequest, obj=None) -> bool:
        return super().has_view_permission(request, obj) or super().has_change_permission(
            request,
            obj,
        )

    def get_actions(self, request: HttpRequest) -> dict:
        return {}


class NoAddDeleteAdminMixin:
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(ConnectorConfig)
class ConnectorConfigAdmin(TimestampedAdmin):
    change_list_template = "admin/connectors/connectorconfig/change_list.html"
    list_display = (
        "name",
        "org",
        "facility",
        "connector_type",
        "is_active",
        "sync_interval_minutes",
        "last_synced_at",
        "created_at",
    )
    list_filter = ("connector_type", "is_active", "org", "facility")
    list_select_related = ("org", "facility")
    search_fields = (
        "name",
        "org__id",
        "org__name",
        "facility__code",
        "facility__name",
    )
    autocomplete_fields = ("org", "facility")
    readonly_fields = TimestampedAdmin.readonly_fields + ("last_synced_at",)
    actions = ("queue_sync_now",)
    fields = (
        "org",
        "name",
        "connector_type",
        "is_active",
        "facility",
        "sync_interval_minutes",
        "enabled_entities",
        "config",
        "last_synced_at",
        "created_at",
        "updated_at",
    )

    @admin.action(description="Queue sync now")
    def queue_sync_now(self, request: HttpRequest, queryset) -> None:
        queued = 0
        errors: list[str] = []

        for connector in queryset.select_related("org", "facility"):
            try:
                services.trigger_sync(connector.org, connector.id)
                queued += 1
            except Exception as exc:
                errors.append(f"{connector.name}: {exc}")

        if queued:
            self.message_user(
                request,
                f"Queued sync for {queued} connector(s).",
                level=messages.SUCCESS,
            )
        if errors:
            self.message_user(
                request,
                f"Failed to queue sync for {len(errors)} connector(s): {'; '.join(errors)}",
                level=messages.ERROR,
            )

    def get_urls(self):
        info = self.opts.app_label, self.opts.model_name
        custom_urls = [
            path(
                "dispatch-due-syncs/",
                self.admin_site.admin_view(self.dispatch_due_syncs_view),
                name=f"{info[0]}_{info[1]}_dispatch_due_syncs",
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request: HttpRequest, extra_context=None):
        extra_context = extra_context or {}
        if self.has_change_permission(request):
            extra_context["dispatch_due_syncs_url"] = reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_dispatch_due_syncs",
                current_app=self.admin_site.name,
            )
        return super().changelist_view(request, extra_context=extra_context)

    def dispatch_due_syncs_view(self, request: HttpRequest):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        if not self.has_change_permission(request):
            raise PermissionDenied

        result = services.dispatch_due_syncs()
        error_count = len(result.get("errors", []))
        message_level = messages.WARNING if error_count else messages.SUCCESS
        self.message_user(
            request,
            (
                "Dispatch due syncs completed: "
                f"queued {result.get('queued', 0)}, "
                f"skipped {result.get('skipped', 0)}, "
                f"errors {error_count}."
            ),
            level=message_level,
        )
        return redirect(
            reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist",
                current_app=self.admin_site.name,
            )
        )


@admin.register(SyncLog)
class SyncLogAdmin(NoAddDeleteAdminMixin, TimestampedAdmin):
    list_display = (
        "connector",
        "org",
        "entity_type",
        "status",
        "started_at",
        "completed_at",
        "records_fetched",
        "records_created",
        "records_updated",
        "records_skipped",
        "records_failed",
        "created_at",
    )
    list_filter = ("status", "entity_type", "connector", "org", "created_at")
    list_select_related = ("connector", "org")
    search_fields = ("=id", "connector__name", "org__id", "org__name")
    readonly_fields = (
        "id",
        "connector",
        "org",
        "entity_type",
        "started_at",
        "completed_at",
        "records_fetched",
        "records_created",
        "records_updated",
        "records_skipped",
        "records_failed",
        "formatted_error_details",
        "formatted_cursor_state",
        "created_at",
        "updated_at",
    )
    fields = (
        "id",
        "connector",
        "org",
        "entity_type",
        "status",
        "started_at",
        "completed_at",
        "records_fetched",
        "records_created",
        "records_updated",
        "records_skipped",
        "records_failed",
        "formatted_error_details",
        "formatted_cursor_state",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"

    @admin.display(description="Error details")
    def formatted_error_details(self, obj: SyncLog) -> str:
        return _format_json(obj.error_details)

    @admin.display(description="Cursor state")
    def formatted_cursor_state(self, obj: SyncLog) -> str:
        return _format_json(obj.cursor_state)

    def save_model(self, request: HttpRequest, obj: SyncLog, form, change: bool) -> None:
        now = timezone.now()
        if obj.status == SyncStatus.PENDING:
            obj.started_at = None
            obj.completed_at = None
        elif obj.status == SyncStatus.RUNNING:
            obj.started_at = obj.started_at or now
            obj.completed_at = None
        elif obj.status in {SyncStatus.COMPLETED, SyncStatus.FAILED}:
            obj.started_at = obj.started_at or now
            obj.completed_at = now
        super().save_model(request, obj, form, change)


@admin.register(ExternalEntityMapping)
class ExternalEntityMappingAdmin(ReadOnlyAdminMixin, TimestampedAdmin):
    list_display = (
        "connector",
        "org",
        "entity_type",
        "external_id",
        "internal_id",
        "external_hash",
        "created_at",
    )
    list_filter = ("entity_type", "connector", "org", "created_at")
    list_select_related = ("connector", "org")
    search_fields = (
        "connector__name",
        "org__id",
        "org__name",
        "external_id",
        "=internal_id",
    )
    readonly_fields = (
        "id",
        "connector",
        "org",
        "entity_type",
        "external_id",
        "internal_id",
        "external_hash",
        "created_at",
        "updated_at",
    )
    fields = readonly_fields
    date_hierarchy = "created_at"
