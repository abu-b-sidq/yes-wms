from django.apps import AppConfig


class OperationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.operations"
    label = "app_operations"
    verbose_name = "WMS Operations"

    def ready(self):
        import app.operations.signals  # noqa: F401
