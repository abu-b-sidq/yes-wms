from django.db import models

from app.core.base_models import TimestampedModel, UUIDPrimaryKeyMixin
from app.core.enums import TransactionType


class TransactionDocumentConfig(UUIDPrimaryKeyMixin, TimestampedModel):
    """
    Multi-level configuration for transaction document generation.

    Resolution order (most specific wins):
      global env flag → org-level → facility-level → transaction-type-level

    A row with org=None and facility=None applies to all orgs/facilities.
    A row with facility=None but org set applies to all facilities in that org.
    transaction_type=None means "all types" for that org/facility scope.
    """

    org = models.ForeignKey(
        "app_masters.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="document_configs",
    )
    facility = models.ForeignKey(
        "app_masters.Facility",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="document_configs",
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        null=True,
        blank=True,
    )
    is_enabled = models.BooleanField(default=True)
    template_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Django template path e.g. 'documents/grn.html'. Leave blank to use the default for the transaction type.",
    )

    class Meta:
        db_table = "app_transaction_document_config"
        constraints = [
            models.UniqueConstraint(
                fields=["org", "facility", "transaction_type"],
                name="uq_doc_config_org_facility_type",
            )
        ]

    def __str__(self) -> str:
        parts = [
            f"org={self.org_id or '*'}",
            f"facility={self.facility_id or '*'}",
            f"type={self.transaction_type or '*'}",
        ]
        status = "enabled" if self.is_enabled else "disabled"
        return f"DocumentConfig({', '.join(parts)}) [{status}]"
