import json
from functools import lru_cache

from app.core.config import get_runtime_settings


class FirebaseInvalidTokenError(Exception):
    pass


class FirebaseVerificationError(Exception):
    pass


class FirebaseTokenVerifier:
    def __init__(self) -> None:
        self._sdk = self._load_sdk()
        self._app = self._initialize_app()

    @staticmethod
    def _load_sdk():
        try:
            import firebase_admin
            from firebase_admin import auth, credentials
            from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError, RevokedIdTokenError
        except ImportError as exc:
            raise FirebaseVerificationError(
                "firebase-admin package is required for Firebase token verification."
            ) from exc

        return {
            "firebase_admin": firebase_admin,
            "auth": auth,
            "credentials": credentials,
            "expired": ExpiredIdTokenError,
            "invalid": InvalidIdTokenError,
            "revoked": RevokedIdTokenError,
        }

    def _initialize_app(self):
        settings = get_runtime_settings()
        firebase_admin = self._sdk["firebase_admin"]
        credentials = self._sdk["credentials"]

        # If the default app is already initialised (e.g. by another worker,
        # the MCP server, or a hot-reload) just reuse it.
        try:
            return firebase_admin.get_app()
        except ValueError:
            pass  # No default app yet — proceed to initialise.

        try:
            if settings.firebase_service_account_json:
                try:
                    credential_payload = json.loads(settings.firebase_service_account_json)
                except json.JSONDecodeError as exc:
                    raise FirebaseVerificationError("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON.") from exc
                credential = credentials.Certificate(credential_payload)
                return firebase_admin.initialize_app(credential, {"projectId": settings.firebase_project_id})

            if settings.firebase_service_account_path:
                credential = credentials.Certificate(settings.firebase_service_account_path)
                return firebase_admin.initialize_app(credential, {"projectId": settings.firebase_project_id})
        except FirebaseVerificationError:
            raise
        except Exception as exc:
            raise FirebaseVerificationError(
                f"Unable to initialize Firebase Admin SDK: {exc!s}"
            ) from exc

        raise FirebaseVerificationError(
            "Missing Firebase credentials. Set FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_PATH."
        )

    def verify(self, token: str) -> dict:
        auth = self._sdk["auth"]
        invalid_error = self._sdk["invalid"]
        expired_error = self._sdk["expired"]
        revoked_error = self._sdk["revoked"]

        try:
            decoded = auth.verify_id_token(token, app=self._app)
            if "uid" not in decoded:
                decoded["uid"] = decoded.get("sub")
            return decoded
        except (invalid_error, expired_error, revoked_error) as exc:
            raise FirebaseInvalidTokenError("Firebase token is invalid.") from exc
        except Exception as exc:  # pragma: no cover - defensive catch for SDK/runtime failures.
            raise FirebaseVerificationError("Failed to verify Firebase token.") from exc


@lru_cache(maxsize=1)
def get_firebase_verifier() -> FirebaseTokenVerifier:
    return FirebaseTokenVerifier()
