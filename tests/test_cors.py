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
