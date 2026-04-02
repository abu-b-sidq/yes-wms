import os

from celery import Celery
from dotenv import load_dotenv

if os.path.isfile("/app/.env"):
    load_dotenv("/app/.env")
else:
    load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wms_middleware.settings")

app = Celery("yes_wms")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
