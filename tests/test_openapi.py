def _path(schema: dict, *candidates: str):
    for candidate in candidates:
        if candidate in schema["paths"]:
            return schema["paths"][candidate]
    raise KeyError(candidates[0])


def _root(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    if parts[:2] == ["api", "v1"]:
        parts = parts[2:]
    return parts[0]


def test_openapi_includes_dual_auth_security(client):
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    schemes = schema["components"]["securitySchemes"]
    assert "bearerAuth" in schemes
    assert "apiKeyAuth" in schemes

    move_post = _path(schema, "/operations/move", "/api/v1/operations/move")["post"]
    assert move_post["security"] == [{"bearerAuth": []}, {"apiKeyAuth": []}]
    move_header_params = {item["name"]: item for item in move_post["parameters"] if item["in"] == "header"}
    assert {"warehouse", "X-Org-Id", "X-Facility-Id", "Authorization", "X-API-Key"} <= set(move_header_params)
    assert move_header_params["warehouse"]["required"] is True
    assert move_header_params["X-Org-Id"]["required"] is True
    assert move_header_params["X-Facility-Id"]["required"] is True

    balances_get = _path(schema, "/inventory/balances", "/api/v1/inventory/balances")["get"]
    assert balances_get["security"] == [{"bearerAuth": []}, {"apiKeyAuth": []}]
    balance_header_params = {item["name"]: item for item in balances_get["parameters"] if item["in"] == "header"}
    assert {"warehouse", "X-Org-Id", "X-Facility-Id", "Authorization", "X-API-Key"} <= set(balance_header_params)
    assert balance_header_params["X-Facility-Id"]["required"] is False

    organizations_post = _path(schema, "/masters/organizations", "/api/v1/masters/organizations")["post"]
    org_header_params = {item["name"] for item in organizations_post["parameters"] if item["in"] == "header"}
    assert {"warehouse", "Authorization", "X-API-Key"} <= org_header_params
    assert "X-Org-Id" not in org_header_params

    allowed_roots = {"health", "masters", "operations", "inventory"}
    actual_roots = {_root(path) for path in schema["paths"]}
    assert actual_roots <= allowed_roots


def test_swagger_ui_is_public(client):
    response = client.get("/api/v1/swagger")
    assert response.status_code == 200
