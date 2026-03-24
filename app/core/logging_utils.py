from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from django.conf import settings as django_settings

from app.core.config import DEFAULT_LOG_REDACT_KEYS
from app.core.context import get_auth_context, get_tenant_context

REDACTED_VALUE = "***REDACTED***"
_RESERVED_LOG_RECORD_FIELDS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_redact_keys(value: str | None) -> tuple[str, ...]:
    if value is None or value.strip() == "":
        return DEFAULT_LOG_REDACT_KEYS

    keys = tuple(dict.fromkeys(chunk.strip().lower() for chunk in value.split(",") if chunk.strip()))
    return keys or DEFAULT_LOG_REDACT_KEYS


def get_log_redact_keys() -> tuple[str, ...]:
    if django_settings.configured and hasattr(django_settings, "LOG_REDACT_KEYS"):
        configured_keys = getattr(django_settings, "LOG_REDACT_KEYS")
        if isinstance(configured_keys, (list, tuple)):
            keys = tuple(str(value).strip().lower() for value in configured_keys if str(value).strip())
            if keys:
                return keys
    return _parse_redact_keys(os.getenv("LOG_REDACT_KEYS"))


def log_include_payloads_enabled() -> bool:
    if django_settings.configured and hasattr(django_settings, "LOG_INCLUDE_PAYLOADS"):
        return bool(getattr(django_settings, "LOG_INCLUDE_PAYLOADS"))
    return _parse_bool(os.getenv("LOG_INCLUDE_PAYLOADS"), True)


def sanitize_for_log(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(key): sanitize_for_log(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize_for_log(item) for item in value]
    if hasattr(value, "model_dump"):
        return sanitize_for_log(value.model_dump())
    if hasattr(value, "dict"):
        return sanitize_for_log(value.dict())
    return str(value)


def _is_sensitive_key(key: str, redact_keys: tuple[str, ...]) -> bool:
    normalized = key.strip().lower()
    return any(candidate in normalized for candidate in redact_keys)


def redact_sensitive(value: Any, redact_keys: tuple[str, ...] | None = None) -> Any:
    keys = redact_keys or get_log_redact_keys()
    sanitized = sanitize_for_log(value)

    if isinstance(sanitized, dict):
        redacted: dict[str, Any] = {}
        for key, child in sanitized.items():
            if _is_sensitive_key(key, keys):
                redacted[key] = REDACTED_VALUE
            else:
                redacted[key] = redact_sensitive(child, keys)
        return redacted
    if isinstance(sanitized, list):
        return [redact_sensitive(item, keys) for item in sanitized]
    return sanitized


def _parse_json_or_text(raw: bytes, content_type: str | None) -> Any:
    decoded = raw.decode("utf-8", errors="replace")
    if content_type and "json" in content_type.lower():
        try:
            return json.loads(decoded)
        except json.JSONDecodeError:
            return decoded

    try:
        return json.loads(decoded)
    except json.JSONDecodeError:
        return decoded


def extract_request_payload(request: Any, include_payloads: bool | None = None) -> dict[str, Any]:
    should_include_payloads = log_include_payloads_enabled() if include_payloads is None else include_payloads

    headers = dict(getattr(request, "headers", {}).items()) if hasattr(request, "headers") else {}
    query = {}
    if hasattr(request, "GET") and hasattr(request.GET, "lists"):
        for key, values in request.GET.lists():
            query[key] = values[0] if len(values) == 1 else values

    body: Any = None
    if should_include_payloads:
        raw_body = getattr(request, "body", b"")
        if raw_body:
            content_type = request.headers.get("Content-Type", "") if hasattr(request, "headers") else ""
            body = _parse_json_or_text(raw_body, content_type)

    payload = {
        "headers": headers,
        "query": query,
        "body": body,
    }
    return redact_sensitive(payload)


def extract_response_payload(response: Any, include_payloads: bool | None = None) -> dict[str, Any]:
    should_include_payloads = log_include_payloads_enabled() if include_payloads is None else include_payloads

    headers = dict(response.items()) if hasattr(response, "items") else {}
    body: Any = None
    if should_include_payloads:
        raw_body = getattr(response, "content", b"")
        if isinstance(raw_body, (bytes, bytearray)) and raw_body:
            content_type = None
            if hasattr(response, "headers"):
                content_type = response.headers.get("Content-Type")
            body = _parse_json_or_text(bytes(raw_body), content_type)

    payload = {
        "headers": headers,
        "body": body,
    }
    return redact_sensitive(payload)


def build_request_context(request: Any) -> dict[str, Any]:
    auth = get_auth_context(request)
    tenant = get_tenant_context(request)
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "") if hasattr(request, "META") else ""
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else ""
    if not client_ip and hasattr(request, "META"):
        client_ip = request.META.get("REMOTE_ADDR", "")

    route = None
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match is not None:
        route = getattr(resolver_match, "route", None) or getattr(resolver_match, "view_name", None)

    context = {
        "request_id": getattr(request, "request_id", None),
        "http": {
            "method": getattr(request, "method", None),
            "path": getattr(request, "path", None),
            "route": route,
            "client_ip": client_ip or None,
            "user_agent": request.headers.get("User-Agent", "") if hasattr(request, "headers") else "",
        },
        "tenant": {
            "warehouse": tenant.warehouse_key,
            "org_id": tenant.org_id,
            "facility_id": tenant.facility_id,
        },
        "auth": {
            "source": auth.auth_source,
            "uid": auth.uid,
            "client_name": auth.client_name,
        },
    }
    return sanitize_for_log(context)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    **event_data: Any,
) -> None:
    logger.log(
        level,
        event,
        extra={
            "event_name": event,
            "event_data": redact_sensitive(event_data),
        },
    )


class JsonLogFormatter(logging.Formatter):
    def __init__(
        self,
        service: str = "rozana-wms",
        environment: str | None = None,
        redact_keys: list[str] | tuple[str, ...] | str | None = None,
    ):
        super().__init__()
        self.service = service
        self.environment = environment or os.getenv("APPLICATION_ENVIRONMENT", "unknown")
        if isinstance(redact_keys, str):
            self.redact_keys = _parse_redact_keys(redact_keys)
        elif isinstance(redact_keys, (list, tuple)):
            keys = tuple(str(value).strip().lower() for value in redact_keys if str(value).strip())
            self.redact_keys = keys or DEFAULT_LOG_REDACT_KEYS
        else:
            self.redact_keys = get_log_redact_keys()

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service,
            "environment": self.environment,
        }

        event_name = getattr(record, "event_name", None)
        if event_name:
            payload["event"] = event_name

        event_data = getattr(record, "event_data", None)
        if isinstance(event_data, dict):
            for key, value in event_data.items():
                if key not in payload:
                    payload[key] = value

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED_LOG_RECORD_FIELDS and key not in {"event_name", "event_data"}
        }
        for key, value in extras.items():
            if key not in payload:
                payload[key] = sanitize_for_log(value)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        safe_payload = redact_sensitive(payload, self.redact_keys)
        return json.dumps(safe_payload, ensure_ascii=True, separators=(",", ":"))
