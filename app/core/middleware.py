import logging
import time
from fnmatch import fnmatch
from urllib.parse import urlparse
from uuid import uuid4

from django.conf import settings
from django.http import HttpResponse
from django.utils.cache import patch_vary_headers

from app.core.context import TenantContext
from app.core.logging_utils import (
    build_request_context,
    extract_request_payload,
    extract_response_payload,
    log_event,
)
from app.core.response import error_response

request_logger = logging.getLogger("app.request")


class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allow_all_origins = getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False)
        self.allowed_origins = set(getattr(settings, "CORS_ALLOWED_ORIGINS", []))
        self.allowed_origin_patterns = tuple(getattr(settings, "CORS_ALLOWED_ORIGIN_PATTERNS", []))
        self.allow_methods = getattr(
            settings,
            "CORS_ALLOW_METHODS",
            ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        )
        self.allow_headers = getattr(
            settings,
            "CORS_ALLOW_HEADERS",
            [
                "Authorization",
                "Content-Type",
                "X-API-Key",
                "warehouse",
                "X-Facility-Id",
                "X-Org-Id",
                "X-Request-ID",
            ],
        )
        self.allow_credentials = getattr(settings, "CORS_ALLOW_CREDENTIALS", True)
        self.max_age = int(getattr(settings, "CORS_PREFLIGHT_MAX_AGE", 86400))

    def __call__(self, request):
        origin = request.headers.get("Origin", "")
        is_preflight = request.method == "OPTIONS" and bool(request.headers.get("Access-Control-Request-Method"))

        if is_preflight and self._is_allowed_origin(origin):
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        if self._is_allowed_origin(origin):
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            response["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            response["Access-Control-Max-Age"] = str(self.max_age)
            if self.allow_credentials:
                response["Access-Control-Allow-Credentials"] = "true"
            patch_vary_headers(response, ("Origin",))

        return response

    def _is_allowed_origin(self, origin: str) -> bool:
        if not origin:
            return False

        if self.allow_all_origins:
            return True

        if origin in self.allowed_origins:
            return True

        if not self.allowed_origin_patterns:
            return False

        parsed_origin = urlparse(origin)
        origin_host = (parsed_origin.hostname or "").lower()
        origin_netloc = parsed_origin.netloc.lower()
        origin_normalized = origin.lower()

        if not origin_host:
            return False

        for pattern in self.allowed_origin_patterns:
            normalized_pattern = pattern.lower()

            # Support full-origin patterns (e.g. https://*.example.com)
            if "://" in normalized_pattern and fnmatch(origin_normalized, normalized_pattern):
                return True
            # Support host:port patterns
            if ":" in normalized_pattern and fnmatch(origin_netloc, normalized_pattern):
                return True
            # Default: match hostname only
            if fnmatch(origin_host, normalized_pattern):
                return True

        return False


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        return response


class RequestLoggingMiddleware:
    API_PREFIX = "/api/v1/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._is_api_path(request.path):
            return self.get_response(request)

        include_payloads = bool(getattr(settings, "LOG_INCLUDE_PAYLOADS", True))
        request_payload = extract_request_payload(request, include_payloads=include_payloads)
        start = time.perf_counter()

        try:
            response = self.get_response(request)
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            context = build_request_context(request)
            log_event(
                request_logger,
                logging.ERROR,
                "api.request.exception",
                **context,
                latency_ms=latency_ms,
                request_payload=request_payload,
                error={"type": exc.__class__.__name__, "message": str(exc)},
            )
            raise

        latency_ms = int((time.perf_counter() - start) * 1000)
        status_code = getattr(response, "status_code", 500)
        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING

        context = build_request_context(request)
        http_context = dict(context.get("http", {}))
        http_context["status_code"] = status_code
        context["http"] = http_context

        log_event(
            request_logger,
            level,
            "api.request.completed",
            **context,
            latency_ms=latency_ms,
            request_payload=request_payload,
            response_payload=extract_response_payload(response, include_payloads=include_payloads),
        )
        return response

    def _is_api_path(self, path: str) -> bool:
        return path.startswith(self.API_PREFIX)


class TenantContextMiddleware:
    API_PREFIX = "/api/v1/"
    EXEMPT_PATHS = (
        "/api/v1/health",
        "/api/v1/docs",
        "/api/v1/swagger",
        "/api/v1/openapi.json",
        # Session bootstrap — called before a facility/warehouse is selected
        "/api/v1/mobile/session/login",
        "/api/v1/mobile/session/select-facility",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._is_api_path(request.path) or self._is_exempt_path(request.path):
            return self.get_response(request)

        warehouse_key = request.headers.get("warehouse", "").strip()
        org_id = request.headers.get("X-Org-Id", "").strip() or None
        facility_id = request.headers.get("X-Facility-Id", "").strip() or None

        if not warehouse_key:
            return error_response(
                request,
                code="TENANT_MISSING_WAREHOUSE",
                message="Missing required `warehouse` header.",
                status_code=400,
            )

        request.tenant_context = TenantContext(
            warehouse_key=warehouse_key,
            org_id=org_id,
            facility_id=facility_id,
        )

        return self.get_response(request)

    def _is_api_path(self, path: str) -> bool:
        return path.startswith(self.API_PREFIX)

    def _is_exempt_path(self, path: str) -> bool:
        return path.startswith(self.EXEMPT_PATHS)
