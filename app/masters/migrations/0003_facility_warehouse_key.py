from django.db import migrations, models


def populate_facility_warehouse_keys(apps, schema_editor):
    Facility = apps.get_model("app_masters", "Facility")
    for facility in Facility.objects.filter(warehouse_key="").iterator():
        facility.warehouse_key = facility.code
        facility.save(update_fields=["warehouse_key"])


class Migration(migrations.Migration):

    dependencies = [
        ("app_masters", "0002_appuser_permission_role_userplatformrole_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="facility",
            name="warehouse_key",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.RunPython(
            populate_facility_warehouse_keys,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="facility",
            constraint=models.UniqueConstraint(
                fields=("org", "warehouse_key"),
                name="uq_facility_org_warehouse_key",
            ),
        ),
    ]
