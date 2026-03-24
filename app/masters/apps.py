from django.apps import AppConfig


class MastersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.masters"
    label = "app_masters"
    verbose_name = "WMS Masters"

    def ready(self):
        import app.masters.signals  # noqa: F401
