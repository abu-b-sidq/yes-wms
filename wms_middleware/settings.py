import os
from pathlib import Path
from typing import Any

from app.core.config import get_runtime_settings

BASE_DIR = Path(__file__).resolve().parent.parent

RUNTIME_SETTINGS = get_runtime_settings()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "*").split(",") if host.strip()]
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DESTINATION = RUNTIME_SETTINGS.log_destination
LOG_FORMAT = RUNTIME_SETTINGS.log_format
LOG_INCLUDE_PAYLOADS = RUNTIME_SETTINGS.log_include_payloads
LOG_REDACT_KEYS = list(RUNTIME_SETTINGS.log_redact_keys)
LOG_FILE_PATH = RUNTIME_SETTINGS.log_file_path
LOG_FILE_MAX_BYTES = RUNTIME_SETTINGS.log_file_max_bytes
LOG_FILE_BACKUP_COUNT = RUNTIME_SETTINGS.log_file_backup_count
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:4200,http://127.0.0.1:4200",
    ).split(",")
    if origin.strip()
]
CORS_ALLOWED_ORIGIN_PATTERNS = [
    pattern.strip().lower()
    for pattern in os.getenv("CORS_ALLOWED_ORIGIN_PATTERNS", "").split(",")
    if pattern.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
DEFAULT_CORS_ALLOW_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-API-Key",
    "warehouse",
    "X-Facility-Id",
    "X-Org-Id",
    "X-Request-ID",
    "company-code",
    "x-geolocation",
    "x-web-version",
]
CORS_ALLOW_HEADERS = [
    header.strip()
    for header in os.getenv("CORS_ALLOW_HEADERS", ",".join(DEFAULT_CORS_ALLOW_HEADERS)).split(",")
    if header.strip()
]
CORS_PREFLIGHT_MAX_AGE = int(os.getenv("CORS_PREFLIGHT_MAX_AGE", "86400"))

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "app.masters",
    "app.operations",
    "app.inventory",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "app.core.middleware.CORSMiddleware",
    "django.middleware.common.CommonMiddleware",
    "app.core.middleware.RequestIDMiddleware",
    "app.core.middleware.RequestLoggingMiddleware",
    "app.auth.middleware.DualAuthMiddleware",
    "app.core.middleware.TenantContextMiddleware",
]

ROOT_URLCONF = "wms_middleware.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    }
]

WSGI_APPLICATION = "wms_middleware.wsgi.application"
ASGI_APPLICATION = "wms_middleware.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
    }
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "/static/"


def _build_logging_handler(formatter_name: str) -> dict[str, Any]:
    if LOG_DESTINATION == "firehose" and RUNTIME_SETTINGS.firehose_delivery_stream_name:
        return {
            "()": "app.core.firehose_handler.FirehoseHandler",
            "delivery_stream_name": RUNTIME_SETTINGS.firehose_delivery_stream_name,
            "region_name": RUNTIME_SETTINGS.firehose_region,
            "batch_size": RUNTIME_SETTINGS.firehose_batch_size,
            "flush_interval_seconds": RUNTIME_SETTINGS.firehose_flush_interval_seconds,
            "formatter": formatter_name,
        }
    if LOG_DESTINATION == "firehose":
        # No FIREHOSE_DELIVERY_STREAM_NAME: fall back to stdout for collectors
        return {
            "class": "logging.StreamHandler",
            "formatter": formatter_name,
        }

    filename = LOG_FILE_PATH
    directory = os.path.dirname(filename)
    if directory:
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError:
            filename = "/tmp/rozana-wms.log"

    return {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": formatter_name,
        "filename": filename,
        "maxBytes": LOG_FILE_MAX_BYTES,
        "backupCount": LOG_FILE_BACKUP_COUNT,
        "encoding": "utf-8",
        "delay": True,
    }


_formatter_name = "json" if LOG_FORMAT == "json" else "standard"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
        "json": {
            "()": "app.core.logging_utils.JsonLogFormatter",
            "service": "rozana-wms",
            "environment": os.getenv("APPLICATION_ENVIRONMENT", "unknown"),
            "redact_keys": LOG_REDACT_KEYS,
        },
    },
    "handlers": {
        "default": _build_logging_handler(_formatter_name),
    },
    "root": {
        "handlers": ["default"],
        "level": "WARNING",
    },
    "loggers": {
        "app": {
            "handlers": ["default"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["default"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
