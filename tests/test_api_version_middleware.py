import json

from django.http import JsonResponse
from django.test import RequestFactory

from app.auth.middleware import DualAuthMiddleware
from app.core.middleware import TenantContextMiddleware


def _ok_response(_request):
    return JsonResponse({"success": True})


def test_public_health_bypasses_auth():
    request = RequestFactory().get("/api/v1/health")
    response = DualAuthMiddleware(_ok_response)(request)

    assert response.status_code == 200


def test_protected_paths_require_auth():
    request = RequestFactory().get(
        "/api/v1/inventory/balances",
        HTTP_WAREHOUSE="TEST_WH9",
        HTTP_X_ORG_ID="testorg",
    )
    response = DualAuthMiddleware(_ok_response)(request)
    body = json.loads(response.content.decode("utf-8"))

    assert response.status_code == 401
    assert body["error"]["code"] == "AUTH_MISSING_CREDENTIAL"


def test_public_openapi_bypasses_warehouse_validation():
    request = RequestFactory().get("/api/v1/openapi.json")
    response = TenantContextMiddleware(_ok_response)(request)

    assert response.status_code == 200


def test_protected_paths_require_warehouse():
    request = RequestFactory().get("/api/v1/inventory/balances")
    response = TenantContextMiddleware(_ok_response)(request)
    body = json.loads(response.content.decode("utf-8"))

    assert response.status_code == 400
    assert body["error"]["code"] == "TENANT_MISSING_WAREHOUSE"


def test_unknown_warehouse_is_rejected():
    request = RequestFactory().get(
        "/api/v1/inventory/balances",
        HTTP_WAREHOUSE="UNKNOWN",
    )
    response = TenantContextMiddleware(_ok_response)(request)
    body = json.loads(response.content.decode("utf-8"))

    assert response.status_code == 400
    assert body["error"]["code"] == "TENANT_UNKNOWN_WAREHOUSE"
