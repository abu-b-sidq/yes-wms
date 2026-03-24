from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.inventory"
    label = "app_inventory"
    verbose_name = "WMS Inventory"
