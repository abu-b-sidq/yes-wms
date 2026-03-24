from django.db import connection


def test_standalone_app_tables_exist(db):
    tables = set(connection.introspection.table_names())

    assert {
        "app_organization",
        "app_facility",
        "app_sku",
        "app_zone",
        "app_location",
        "app_facility_sku",
        "app_facility_zone",
        "app_facility_location",
        "app_transaction",
        "app_pick",
        "app_drop",
        "app_inventory_balance",
        "app_inventory_ledger",
    } <= tables
    assert not any(table.startswith("v2_") for table in tables)
