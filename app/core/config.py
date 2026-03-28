from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

DEFAULT_LOG_REDACT_KEYS = (
    "authorization",
    "x-api-key",
    "api_key",
    "token",
    "access_token",
    "refresh_token",
    "client_secret",
    "password",
    "secret",
    "private_key",
    "firebase_service_account_json",
)

ALLOWED_LOG_DESTINATIONS = {"firehose", "file"}
ALLOWED_LOG_FORMATS = {"json", "text"}


@dataclass(frozen=True)
class RuntimeSettings:
    firebase_service_account_json: str | None
    firebase_service_account_path: str | None
    firebase_project_id: str | None
    firebase_storage_bucket: str | None
    bootstrap_platform_admin_uids: tuple[str, ...]
    auth_fallback_enabled: bool
    legacy_api_keys: dict[str, str]
    document_generation_enabled: bool
    log_destination: str
    log_format: str
    log_include_payloads: bool
    log_redact_keys: tuple[str, ...]
    log_file_path: str
    log_file_max_bytes: int
    log_file_backup_count: int
    firehose_delivery_stream_name: str
    firehose_region: str | None
    firehose_batch_size: int
    firehose_flush_interval_seconds: float


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_json(value: str | None, default: Any) -> Any:
    if value is None or value.strip() == "":
        return default
    return json.loads(value)


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def _parse_log_destination(value: str | None) -> str:
    candidate = (value or "").strip().lower()
    if candidate in ALLOWED_LOG_DESTINATIONS:
        return candidate
    return "file"


def _parse_log_format(value: str | None) -> str:
    candidate = (value or "").strip().lower()
    if candidate in ALLOWED_LOG_FORMATS:
        return candidate
    return "json"


def _parse_log_redact_keys(value: str | None) -> tuple[str, ...]:
    if value is None or value.strip() == "":
        return DEFAULT_LOG_REDACT_KEYS

    keys = tuple(
        dict.fromkeys(chunk.strip().lower() for chunk in value.split(",") if chunk.strip())
    )
    return keys or DEFAULT_LOG_REDACT_KEYS


def _parse_legacy_api_keys(value: str | None) -> dict[str, str]:
    if not value:
        return {}

    try:
        decoded = _parse_json(value, {})
    except json.JSONDecodeError:
        decoded = None

    if isinstance(decoded, dict):
        # Input format: {"client_name": "api_key"}
        return {str(api_key): str(client_name) for client_name, api_key in decoded.items()}

    if isinstance(decoded, list):
        return {str(api_key): f"client_{index + 1}" for index, api_key in enumerate(decoded)}

    keys = [chunk.strip() for chunk in value.split(",") if chunk.strip()]
    return {api_key: f"client_{index + 1}" for index, api_key in enumerate(keys)}


def _parse_uid_list(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()

    try:
        decoded = _parse_json(value, [])
    except json.JSONDecodeError:
        decoded = None

    if isinstance(decoded, list):
        return tuple(dict.fromkeys(str(item).strip() for item in decoded if str(item).strip()))

    return tuple(dict.fromkeys(chunk.strip() for chunk in value.split(",") if chunk.strip()))


@lru_cache(maxsize=1)
def get_runtime_settings() -> RuntimeSettings:
    # Default to baked-in path from CI (same pattern as cart: secret from GitHub → file at build)
    firebase_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if not firebase_path and not os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"):
        _default_path = "/app/auth/firebase_service_account.json"
        if os.path.isfile(_default_path):
            firebase_path = _default_path

    log_destination = _parse_log_destination(os.getenv("LOG_DESTINATION"))
    log_format = _parse_log_format(os.getenv("LOG_FORMAT"))
    log_file_path = os.getenv("LOG_FILE_PATH", "/app/logs/yes-wms.log").strip() or "/app/logs/yes-wms.log"
    firehose_stream = (os.getenv("FIREHOSE_DELIVERY_STREAM_NAME") or "").strip()
    firehose_region = (os.getenv("FIREHOSE_AWS_REGION") or os.getenv("AWS_REGION") or "").strip() or None
    firehose_batch_size = max(1, min(500, _parse_int(os.getenv("FIREHOSE_BATCH_SIZE"), 10)))
    try:
        firehose_flush = float(os.getenv("FIREHOSE_FLUSH_INTERVAL_SECONDS", "5").strip())
    except ValueError:
        firehose_flush = 5.0
    firehose_flush_interval_seconds = max(1.0, min(300.0, firehose_flush))

    firebase_storage_bucket = (os.getenv("FIREBASE_STORAGE_BUCKET") or "").strip() or None

    return RuntimeSettings(
        firebase_service_account_json=os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"),
        firebase_service_account_path=firebase_path,
        firebase_project_id=os.getenv("FIREBASE_PROJECT_ID"),
        firebase_storage_bucket=firebase_storage_bucket,
        bootstrap_platform_admin_uids=_parse_uid_list(os.getenv("BOOTSTRAP_PLATFORM_ADMIN_UIDS")),
        auth_fallback_enabled=_parse_bool(os.getenv("AUTH_FALLBACK_ENABLED"), True),
        document_generation_enabled=_parse_bool(os.getenv("DOCUMENT_GENERATION_ENABLED"), False),
        legacy_api_keys=_parse_legacy_api_keys(os.getenv("LEGACY_API_KEYS")),
        log_destination=log_destination,
        log_format=log_format,
        log_include_payloads=_parse_bool(os.getenv("LOG_INCLUDE_PAYLOADS"), True),
        log_redact_keys=_parse_log_redact_keys(os.getenv("LOG_REDACT_KEYS")),
        log_file_path=log_file_path,
        log_file_max_bytes=max(1, _parse_int(os.getenv("LOG_FILE_MAX_BYTES"), 52_428_800)),
        log_file_backup_count=max(1, _parse_int(os.getenv("LOG_FILE_BACKUP_COUNT"), 10)),
        firehose_delivery_stream_name=firehose_stream,
        firehose_region=firehose_region,
        firehose_batch_size=firehose_batch_size,
        firehose_flush_interval_seconds=firehose_flush_interval_seconds,
    )
