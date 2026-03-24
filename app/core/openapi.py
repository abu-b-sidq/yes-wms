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


def protected_openapi_extra(
    *,
    require_org: bool = True,
    require_facility: bool = False,
    include_facility: bool | None = None,
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

    return {
        "security": copy.deepcopy(PROTECTED_SECURITY),
        "parameters": params,
    }


# ---------------------------------------------------------------------------
# Response schema components — injected globally via inject_security_schemes
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

# Maps path prefix → data schema for the 200 response envelope.
# Populated by route modules via register_response_schema().
_RESPONSE_SCHEMAS: dict[str, dict] = {}


def register_response_schema(operation_id: str, data_schema: dict) -> None:
    """Register a data schema for an operation's 200 response envelope."""
    _RESPONSE_SCHEMAS[operation_id] = data_schema


def _make_envelope(data_schema: dict) -> dict:
    return {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "data": data_schema,
            "error": _ERROR_SCHEMA,
            "meta": _META_SCHEMA,
        },
    }


def inject_security_schemes(schema: dict) -> dict:
    # Security scheme components
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

    # Post-process every operation's responses
    for _path, path_item in schema.get("paths", {}).items():
        for _method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue

            operation_id = operation.get("operationId", "")
            data_schema = _RESPONSE_SCHEMAS.get(operation_id, {"type": "object"})

            # Replace the 200 response — remove both int and str variants Ninja may write
            responses = operation.setdefault("responses", {})
            responses.pop(200, None)
            responses.pop("200", None)
            responses["200"] = {
                "description": "Success",
                "content": {
                    "application/json": {
                        "schema": _make_envelope(data_schema),
                    }
                },
            }

            # Add standard error responses (only if operation has security — i.e. protected)
            if operation.get("security"):
                # Remove Ninja's integer-keyed 422 before setting our string-keyed version
                for code in (401, 403, 404, 422):
                    responses.pop(code, None)
                responses.setdefault("401", {"description": "Unauthorised — missing or invalid credentials."})
                responses.setdefault("403", {"description": "Forbidden — valid credentials but insufficient permissions."})
                responses.setdefault("404", {"description": "Resource not found."})
                responses.setdefault("422", {"description": "Validation error — request body or parameters are invalid."})

    return schema
