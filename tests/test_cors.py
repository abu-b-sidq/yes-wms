from django.test import Client, override_settings


def test_cors_allows_localhost_4200_origin(client):
    response = client.get("/api/v1/health", HTTP_ORIGIN="http://localhost:4200")

    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == "http://localhost:4200"


def test_cors_preflight_options_bypasses_auth(client):
    response = client.options(
        "/api/v1/inventory/balances",
        HTTP_ORIGIN="http://localhost:4200",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
    )

    assert response.status_code == 204
    assert response["Access-Control-Allow-Origin"] == "http://localhost:4200"
    assert "GET" in response["Access-Control-Allow-Methods"]


def test_cors_rejects_unknown_origin_by_default(client):
    response = client.get("/api/v1/health", HTTP_ORIGIN="https://frontend.example.test")

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=True,
    CORS_ALLOWED_ORIGINS=[],
    CORS_ALLOWED_ORIGIN_PATTERNS=[],
)
def test_cors_allows_any_origin_when_allow_all_enabled():
    client = Client()

    response = client.get("/api/v1/health", HTTP_ORIGIN="https://frontend.example.test")

    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == "https://frontend.example.test"
