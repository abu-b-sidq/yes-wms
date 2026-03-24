from decimal import Decimal

import pytest


pytestmark = pytest.mark.django_db


def test_organization_routes_are_not_org_scoped(client, api_headers):
    response = client.post(
        "/api/v1/masters/organizations",
        data={"id": "neworg", "name": "New Org"},
        content_type="application/json",
        **api_headers(org_id=None, facility_id=None),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == "neworg"
    assert body["meta"]["warehouse_key"] == "TEST_WH9"


def test_facility_routes_require_org_and_return_meta(client, org, api_headers):
    response = client.post(
        "/api/v1/masters/facilities",
        data={"code": "FAC-NEW", "name": "New Facility"},
        content_type="application/json",
        **api_headers(org_id=org.id, facility_id=None),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["code"] == "FAC-NEW"
    assert body["meta"]["org_id"] == org.id
    assert body["meta"]["auth_source"] == "api_key"


def test_operations_and_inventory_flow(client, org, facility, sku, zone, location, location2, api_headers):
    headers = api_headers(org_id=org.id, facility_id=facility.code)

    grn_response = client.post(
        "/api/v1/operations/grn",
        data={"items": [{"sku_code": sku.code, "quantity": "10"}]},
        content_type="application/json",
        **headers,
    )
    assert grn_response.status_code == 200
    assert grn_response.json()["data"]["transaction_type"] == "GRN"

    putaway_response = client.post(
        "/api/v1/operations/putaway",
        data={
            "sku_code": sku.code,
            "dest_entity_code": location.code,
            "quantity": "10",
        },
        content_type="application/json",
        **headers,
    )
    assert putaway_response.status_code == 200
    assert putaway_response.json()["data"]["transaction_type"] == "PUTAWAY"

    balances_response = client.get(
        f"/api/v1/inventory/balances/by-location/{location.code}",
        **headers,
    )
    assert balances_response.status_code == 200
    balances = balances_response.json()["data"]
    assert len(balances) == 1
    assert Decimal(balances[0]["quantity_on_hand"]) == Decimal("10.0000")


def test_transactions_list_allows_optional_facility_filter(client, org, facility, sku, api_headers):
    headers = api_headers(org_id=org.id, facility_id=facility.code)
    client.post(
        "/api/v1/operations/grn",
        data={"items": [{"sku_code": sku.code, "quantity": "5"}]},
        content_type="application/json",
        **headers,
    )

    list_response = client.get("/api/v1/operations/transactions", **api_headers(org_id=org.id, facility_id=None))

    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) >= 1
