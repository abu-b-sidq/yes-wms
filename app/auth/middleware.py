from __future__ import annotations

from app.auth.api_key import LegacyAPIKeyVerifier
from app.auth.firebase_verifier import (
    FirebaseInvalidTokenError,
    FirebaseVerificationError,
    get_firebase_verifier,
)
from app.auth.user_sync import sync_firebase_user
from app.core.config import get_runtime_settings
from app.core.context import AuthContext
from app.core.response import error_response


class DualAuthMiddleware:
    API_PREFIX = "/api/v1/"
    EXEMPT_PATHS = (
        "/api/v1/operations/mobile/session/login",
        "/api/v1/health",
        "/api/v1/docs",
        "/api/v1/swagger",
        "/api/v1/openapi.json",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        settings = get_runtime_settings()
        if not self._is_api_path(request.path) or self._is_exempt_path(request.path):
            return self.get_response(request)

        auth_header = request.headers.get("Authorization", "").strip()
        firebase_token = self._extract_token(auth_header)
        firebase_error = None

        if firebase_token:
            try:
                claims = get_firebase_verifier().verify(firebase_token)
                app_user = sync_firebase_user(claims)
                request.auth_context = AuthContext(
                    is_authenticated=True,
                    auth_source="firebase",
                    uid=claims.get("uid"),
                    app_user_id=str(app_user.id),
                    email=app_user.email or None,
                    user_status=app_user.status,
                    claims=claims,
                )
                return self.get_response(request)
            except FirebaseInvalidTokenError as exc:
                firebase_error = ("AUTH_FIREBASE_INVALID_TOKEN", str(exc))
            except FirebaseVerificationError as exc:
                firebase_error = ("AUTH_FIREBASE_VERIFICATION_FAILED", str(exc))

        if settings.auth_fallback_enabled:
            api_key = request.headers.get("X-API-Key", "").strip()
            if api_key:
                verifier = LegacyAPIKeyVerifier(settings.legacy_api_keys)
                client_name = verifier.verify(api_key)
                if client_name:
                    request.auth_context = AuthContext(
                        is_authenticated=True,
                        auth_source="api_key",
                        client_name=client_name,
                    )
                    return self.get_response(request)
                if firebase_error is None:
                    return error_response(
                        request,
                        code="AUTH_API_KEY_INVALID",
                        message="X-API-Key is invalid.",
                        status_code=401,
                    )

        if firebase_error is not None:
            return error_response(
                request,
                code=firebase_error[0],
                message=firebase_error[1],
                status_code=401,
            )

        return error_response(
            request,
            code="AUTH_MISSING_CREDENTIAL",
            message="Missing Authorization header or valid fallback X-API-Key.",
            status_code=401,
        )

    @staticmethod
    def _extract_token(auth_header: str) -> str | None:
        if not auth_header:
            return None

        parts = auth_header.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
            return token if token else None

        return auth_header.strip() or None

    def _is_exempt_path(self, path: str) -> bool:
        return path.startswith(self.EXEMPT_PATHS)

    def _is_api_path(self, path: str) -> bool:
        return path.startswith(self.API_PREFIX)
