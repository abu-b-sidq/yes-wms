import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("app_masters", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TransactionDocumentConfig",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "transaction_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("MOVE", "Move"),
                            ("ORDER_PICK", "Order Pick"),
                            ("GRN", "Goods Received Note"),
                            ("PUTAWAY", "Putaway"),
                            ("RETURN", "Return"),
                            ("CYCLE_COUNT", "Cycle Count"),
                            ("ADJUSTMENT", "Adjustment"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                ("is_enabled", models.BooleanField(default=True)),
                (
                    "template_name",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Django template path e.g. 'documents/grn.html'. Leave blank to use the default for the transaction type.",
                        max_length=100,
                    ),
                ),
                (
                    "facility",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="document_configs",
                        to="app_masters.facility",
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="document_configs",
                        to="app_masters.organization",
                    ),
                ),
            ],
            options={
                "db_table": "app_transaction_document_config",
            },
        ),
        migrations.AddConstraint(
            model_name="transactiondocumentconfig",
            constraint=models.UniqueConstraint(
                fields=["org", "facility", "transaction_type"],
                name="uq_doc_config_org_facility_type",
                nulls_distinct=False,
            ),
        ),
    ]
