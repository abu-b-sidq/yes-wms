from __future__ import annotations

import copy

WAREHOUSE_HEADER_PARAM = {
    "name": "warehouse",
    "in": "header",
    "required": True,
    "schema": {"type": "string"},
    "description": "Warehouse tenant key.",
    "example": "TEST_WH9",
}

ORG_HEADER_PARAM = {
    "name": "X-Org-Id",
    "in": "header",
    "required": True,
    "schema": {"type": "string"},
    "description": "Organization identifier for org-scoped operations.",
    "example": "testorg",
}

FACILITY_HEADER_PARAM = {
    "name": "X-Facility-Id",
    "in": "header",
    "required": True,
    "schema": {"type": "string"},
    "description": "Facility code for facility-scoped operations.",
    "example": "FAC-001",
}

AUTHORIZATION_HEADER_PARAM = {
    "name": "Authorization",
    "in": "header",
    "required": False,
    "schema": {"type": "string"},
    "description": "Firebase ID token. Supports either `Bearer <token>` or raw token value.",
    "example": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Ii...",
}

API_KEY_HEADER_PARAM = {
    "name": "X-API-Key",
    "in": "header",
    "required": False,
    "schema": {"type": "string"},
    "description": "Legacy auth fallback key.",
    "example": "legacy-secret",
}

PROTECTED_SECURITY = [{"bearerAuth": []}, {"apiKeyAuth": []}]

# ---------------------------------------------------------------------------
# Reusable inline response-body schemas for openapi_extra["responses"]
# ---------------------------------------------------------------------------

_META_SCHEMA = {
    "type": "object",
    "properties": {
        "request_id": {"type": "string"},
        "warehouse_key": {"type": "string"},
        "org_id": {"type": "string", "nullable": True},
        "facility_id": {"type": "string", "nullable": True},
        "auth_source": {"type": "string", "enum": ["bearer", "api_key", "none"]},
        "uid": {"type": "string"},
        "client_name": {"type": "string"},
    },
}

_ERROR_SCHEMA = {
    "type": "object",
    "nullable": True,
    "properties": {
        "code": {"type": "string"},
        "message": {"type": "string"},
        "details": {},
    },
}

_SUCCESS_RESPONSES = {
    "401": {"description": "Unauthorised — missing or invalid auth credentials."},
    "403": {"description": "Forbidden — valid auth but insufficient permissions."},
    "404": {"description": "Not found."},
    "422": {"description": "Validation error — request body or parameters are invalid."},
}


def success_response_schema(data_schema: dict, description: str = "Success") -> dict:
    """Return an ``openapi_extra['responses']`` dict with the standard success envelope."""
    return {
        "responses": {
            "200": {
                "description": description,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean", "example": True},
                                "data": data_schema,
                                "error": _ERROR_SCHEMA,
                                "meta": _META_SCHEMA,
                            },
                        }
                    }
                },
            },
            **_SUCCESS_RESPONSES,
        }
    }


def protected_openapi_extra(
    *,
    require_org: bool = True,
    require_facility: bool = False,
    include_facility: bool | None = None,
    response_schema: dict | None = None,
) -> dict:
    params = [
        copy.deepcopy(WAREHOUSE_HEADER_PARAM),
    ]
    if require_org:
        params.append(copy.deepcopy(ORG_HEADER_PARAM))

    if include_facility is None:
        include_facility = require_facility
    if include_facility:
        facility_param = copy.deepcopy(FACILITY_HEADER_PARAM)
        facility_param["required"] = require_facility
        params.append(facility_param)

    params.extend(
        [
            copy.deepcopy(AUTHORIZATION_HEADER_PARAM),
            copy.deepcopy(API_KEY_HEADER_PARAM),
        ]
    )

    extra: dict = {
        "security": copy.deepcopy(PROTECTED_SECURITY),
        "parameters": params,
    }
    if response_schema is not None:
        extra.update(response_schema)
    return extra


def inject_security_schemes(schema: dict) -> dict:
    components = schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})

    security_schemes["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Primary auth. Use Firebase ID token in Authorization header.",
    }
    security_schemes["apiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Fallback auth for trusted clients when Firebase tokens are unavailable.",
    }

    return schema
