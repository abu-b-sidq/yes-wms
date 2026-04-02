from django.db import models

from app.core.base_models import TenantAwareModel, TimestampedModel, UUIDPrimaryKeyMixin
from app.connectors.enums import ConnectorType, SyncEntityType, SyncStatus


class ConnectorConfig(TenantAwareModel):
    name = models.CharField(max_length=100)
    connector_type = models.CharField(
        max_length=20,
        choices=ConnectorType.choices,
    )
    is_active = models.BooleanField(default=True)
    facility = models.ForeignKey(
        "app_masters.Facility",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="connector_configs",
    )
    config = models.JSONField(
        default=dict,
        help_text="Connection credentials: base_url, client_id, client_secret, warehouse_key, etc.",
    )
    sync_interval_minutes = models.IntegerField(default=60)
    enabled_entities = models.JSONField(
        default=list,
        help_text='List of entity types to sync, e.g. ["SKU", "INVENTORY", "ORDER"]',
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "app_connector_config"
        constraints = [
            models.UniqueConstraint(
                fields=["org", "name"],
                name="uq_connector_config_org_name",
            ),
        ]

    def __str__(self):
        return f"{self.org_id}/{self.name} ({self.connector_type})"


class SyncLog(UUIDPrimaryKeyMixin, TimestampedModel):
    connector = models.ForeignKey(
        ConnectorConfig,
        on_delete=models.CASCADE,
        related_name="sync_logs",
    )
    org = models.ForeignKey(
        "app_masters.Organization",
        on_delete=models.CASCADE,
        related_name="connector_sync_logs",
    )
    entity_type = models.CharField(
        max_length=30,
        choices=SyncEntityType.choices,
    )
    status = models.CharField(
        max_length=20,
        choices=SyncStatus.choices,
        default=SyncStatus.PENDING,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_fetched = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_skipped = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    error_details = models.JSONField(null=True, blank=True)
    cursor_state = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "app_sync_log"
        indexes = [
            models.Index(
                fields=["connector", "entity_type", "created_at"],
                name="idx_sync_log_connector_entity",
            ),
        ]

    def __str__(self):
        return (
            f"SyncLog({self.connector.name} / {self.entity_type} "
            f"— {self.status})"
        )


class ExternalEntityMapping(UUIDPrimaryKeyMixin, TimestampedModel):
    org = models.ForeignKey(
        "app_masters.Organization",
        on_delete=models.CASCADE,
        related_name="external_entity_mappings",
    )
    connector = models.ForeignKey(
        ConnectorConfig,
        on_delete=models.CASCADE,
        related_name="entity_mappings",
    )
    entity_type = models.CharField(max_length=30, choices=SyncEntityType.choices)
    external_id = models.CharField(max_length=255)
    internal_id = models.UUIDField()
    external_hash = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "app_external_entity_mapping"
        constraints = [
            models.UniqueConstraint(
                fields=["connector", "entity_type", "external_id"],
                name="uq_ext_entity_mapping",
            ),
        ]
        indexes = [
            models.Index(
                fields=["connector", "entity_type"],
                name="idx_ext_mapping_connector_type",
            ),
        ]

    def __str__(self):
        return (
            f"Mapping({self.entity_type}: {self.external_id} → {self.internal_id})"
        )
