from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from django.http import JsonResponse

from app.core.context import get_auth_context, get_tenant_context
from app.core.logging_utils import build_request_context, log_event

response_logger = logging.getLogger("app.response")


def _request_id(request: Any) -> str:
    value = getattr(request, "request_id", None)
    if value:
        return str(value)
    generated = str(uuid4())
    setattr(request, "request_id", generated)
    return generated


def build_meta(request: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    tenant = get_tenant_context(request)
    auth = get_auth_context(request)

    meta: dict[str, Any] = {
        "request_id": _request_id(request),
        "warehouse_key": tenant.warehouse_key,
        "org_id": tenant.org_id,
        "facility_id": tenant.facility_id,
        "auth_source": auth.auth_source,
    }

    if auth.uid:
        meta["uid"] = auth.uid
    if auth.client_name:
        meta["client_name"] = auth.client_name

    if extra:
        meta.update(extra)

    return meta


def success_response(request: Any, data: Any, extra_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": build_meta(request, extra_meta),
    }


def error_response(
    request: Any,
    code: str,
    message: str,
    status_code: int,
    details: Any | None = None,
    extra_meta: dict[str, Any] | None = None,
) -> JsonResponse:
    payload = {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": build_meta(request, extra_meta),
    }

    level = logging.WARNING if 400 <= status_code < 500 else logging.ERROR
    context = build_request_context(request)
    http_context = dict(context.get("http", {}))
    http_context["status_code"] = status_code
    context["http"] = http_context

    log_event(
        response_logger,
        level,
        "api.error.response",
        **context,
        error=payload["error"],
        response_payload=payload,
    )
    return JsonResponse(payload, status=status_code)
