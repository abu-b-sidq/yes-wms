from django.contrib import admin

from app.ai.models import Conversation, EmbeddingRecord, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("id", "role", "content", "components", "tool_calls", "tool_results", "token_count", "created_at")
    fields = ("role", "content", "components", "tool_calls", "created_at")
    ordering = ("created_at",)
    can_delete = False
    show_change_link = True
    max_num = 0  # read-only inline — no add row


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "org", "user", "model_provider", "model_name", "is_active", "created_at", "updated_at")
    list_filter = ("model_provider", "is_active", "org")
    search_fields = ("title", "user__firebase_uid", "user__email", "model_name")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-updated_at",)
    inlines = [MessageInline]
    fieldsets = (
        (None, {
            "fields": ("id", "title", "org", "user", "facility", "is_active"),
        }),
        ("Model", {
            "fields": ("model_provider", "model_name"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "short_content", "token_count", "created_at")
    list_filter = ("role",)
    search_fields = ("content", "conversation__title")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
    fieldsets = (
        (None, {
            "fields": ("id", "conversation", "role", "content", "token_count"),
        }),
        ("Structured Data", {
            "fields": ("components", "tool_calls", "tool_results"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.display(description="Content")
    def short_content(self, obj):
        return obj.content[:80] if obj.content else ""


@admin.register(EmbeddingRecord)
class EmbeddingRecordAdmin(admin.ModelAdmin):
    list_display = ("content_type", "object_id", "org_id", "updated_at")
    list_filter = ("content_type", "org_id")
    search_fields = ("object_id", "org_id", "text")
    readonly_fields = ("updated_at", "embedding_preview")
    ordering = ("-updated_at",)
    fieldsets = (
        (None, {
            "fields": ("content_type", "object_id", "org_id", "text"),
        }),
        ("Vector", {
            "fields": ("embedding_preview",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("updated_at",),
        }),
    )

    @admin.display(description="Embedding")
    def embedding_preview(self, obj):
        if obj is None or obj.embedding is None:
            return ""

        preview = ", ".join(f"{value:.4f}" for value in obj.embedding[:8])
        if len(obj.embedding) > 8:
            preview = f"{preview}, ..."
        return f"{len(obj.embedding)} dims [{preview}]"
