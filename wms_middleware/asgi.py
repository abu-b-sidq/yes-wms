import os

from dotenv import load_dotenv

# Load .env so FIREBASE_SERVICE_ACCOUNT_PATH etc. are available (e.g. when mounted in k8s at /app/.env)
if os.path.isfile("/app/.env"):
    load_dotenv("/app/.env")
else:
    load_dotenv()

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wms_middleware.settings")

application = get_asgi_application()
