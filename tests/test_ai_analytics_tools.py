from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ai import tool_executor
from app.ai.tool_definitions import get_openai_tools
from app.core.exceptions import AuthorizationError, ValidationError
from app.mcp import analytics
from app.mcp import server as mcp_server
from app.mcp import tools as mcp_tools


def test_describe_schema_includes_expected_tables_and_excludes_out_of_scope_tables(db):
    result = analytics.describe_schema()

    table_names = {table["table_name"] for table in result["tables"]}
    assert result["table_count"] == len(result["tables"])
    assert {
        "app_organization",
        "app_facility",
        "app_transaction",
        "app_inventory_balance",
        "app_inventory_ledger",
    } <= table_names
    assert "app_connector_config" not in table_names
    assert "app_user" not in table_names
    assert "app_device_token" not in table_names


def test_describe_schema_contains_business_scope_foreign_keys_and_join_hints(db):
    result = analytics.describe_schema(["app_transaction", "app_inventory_balance"])
    tables = {table["table_name"]: table for table in result["tables"]}

    transaction = tables["app_transaction"]
    assert transaction["domain"] == "operations"
    assert transaction["business_description"]
    assert transaction["scope"]["org_scoped"] is True
    assert transaction["scope"]["facility_scoped"] is True
    assert "facility_id" in transaction["scope"]["scope_columns"]
    assert any(fk["references_table"] == "app_facility" for fk in transaction["foreign_keys"])
    assert any(index["name"] == "idx_txn_org_fac_type_status" for index in transaction["indexes"])
    assert transaction["join_hints"]

    balance = tables["app_inventory_balance"]
    assert balance["domain"] == "inventory"
    assert balance["business_description"]
    assert balance["scope"]["facility_scoped"] is True
    assert any(column["column"] == "quantity_on_hand" for column in balance["columns"])
    assert any(fk["references_table"] == "app_sku" for fk in balance["foreign_keys"])
    assert balance["join_hints"]


def test_validate_analytical_sql_accepts_with_queries_and_tracks_ctes():
    result = analytics.validate_analytical_sql(
        """
        WITH txn_counts AS (
            SELECT transaction_type, COUNT(*) AS total
            FROM app_transaction
            GROUP BY transaction_type
        )
        SELECT *
        FROM txn_counts
        """
    )

    assert result["allowed_tables"] == ["app_transaction"]
    assert result["cte_names"] == ["txn_counts"]


@pytest.mark.parametrize(
    ("sql", "message"),
    [
        ("DELETE FROM app_transaction", "must start with SELECT or WITH"),
        ("SELECT * FROM app_transaction; SELECT * FROM app_sku", "Semicolons"),
        ("SELECT * FROM app_transaction -- comment", "comments"),
        ("SELECT * FROM public.app_transaction", "Schema-qualified"),
        ("SELECT * FROM app_connector_config", "disallowed relations"),
        ("SELECT 1", "must reference at least one allowed table"),
        ("WITH sample AS (SELECT 1) SELECT * FROM sample", "must read from at least one allowed warehouse table"),
    ],
)
def test_validate_analytical_sql_rejects_invalid_queries(sql: str, message: str):
    with pytest.raises(ValidationError, match=message):
        analytics.validate_analytical_sql(sql)


def test_execute_analytical_query_wraps_sql_with_scoped_ctes_and_parameters(monkeypatch):
    captured: dict[str, object] = {}

    class FakeCursor:
        description = [("transaction_type",), ("total",)]

        def execute(self, sql, params):
            captured["sql"] = sql
            captured["params"] = params

        def fetchall(self):
            return [
                ("MOVE", 4),
                ("GRN", 2),
                ("PUTAWAY", 1),
            ]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(analytics.connection, "cursor", lambda: FakeCursor())

    result = analytics.execute_analytical_query(
        sql=(
            "SELECT transaction_type, COUNT(*) AS total "
            "FROM app_transaction "
            "GROUP BY transaction_type"
        ),
        org_id="testorg",
        facility_code="FAC-001",
        facility_pk="fac-uuid-1",
        limit=2,
    )

    assert 'WITH app_transaction AS (' in captured["sql"]
    assert 'FROM "app_transaction" WHERE org_id = %s AND facility_id = %s' in captured["sql"]
    assert "testorg" not in captured["sql"]
    assert "fac-uuid-1" not in captured["sql"]
    assert captured["params"] == ["testorg", "fac-uuid-1", 3]
    assert result["columns"] == ["transaction_type", "total"]
    assert result["rows"] == [
        {"transaction_type": "MOVE", "total": 4},
        {"transaction_type": "GRN", "total": 2},
    ]
    assert result["row_count"] == 2
    assert result["truncated"] is True
    assert result["scope_applied"]["facility_code"] == "FAC-001"


def test_execute_analytical_query_normalizes_decimal_datetime_and_uuid_values(monkeypatch):
    class FakeCursor:
        description = [("quantity",), ("captured_at",), ("row_id",)]

        def execute(self, sql, params):
            return None

        def fetchall(self):
            return [
                (
                    Decimal("12.5000"),
                    datetime(2026, 4, 5, 18, 32, 41, tzinfo=timezone.utc),
                    uuid4(),
                )
            ]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(analytics.connection, "cursor", lambda: FakeCursor())

    result = analytics.execute_analytical_query(
        sql="SELECT quantity, captured_at, row_id FROM app_transaction",
        org_id="testorg",
        facility_code="FAC-001",
        facility_pk="fac-uuid-1",
        limit=10,
    )

    row = result["rows"][0]
    assert row["quantity"] == "12.5000"
    assert row["captured_at"] == "2026-04-05T18:32:41+00:00"
    assert isinstance(row["row_id"], str)


def test_analytics_tool_requires_active_facility_for_facility_restricted_users(monkeypatch):
    monkeypatch.setattr(
        "app.mcp.tools._require_analytics_access",
        lambda uid, org_id: SimpleNamespace(allowed_facility_codes={"FAC-001"}),
    )

    with pytest.raises(AuthorizationError, match="Facility-restricted users must specify facility_id"):
        asyncio.run(
            mcp_tools.wms_execute_analytical_query(
                org_id="testorg",
                sql="SELECT * FROM app_transaction",
                uid="firebase-user-1",
            )
        )


def test_openai_tool_definitions_include_analytics_tools_without_auto_injected_context():
    tools = {tool["function"]["name"]: tool["function"] for tool in get_openai_tools()}

    assert "wms_describe_schema" in tools
    assert "wms_execute_analytical_query" in tools
    assert "org_id" not in tools["wms_describe_schema"]["parameters"]["properties"]
    assert "org_id" not in tools["wms_execute_analytical_query"]["parameters"]["properties"]
    assert "facility_id" not in tools["wms_execute_analytical_query"]["parameters"]["properties"]
    assert "sql" in tools["wms_execute_analytical_query"]["parameters"]["properties"]


def test_execute_tool_dispatches_analytics_tool_with_auto_injected_facility(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_query(sql, org_id, facility_id=None, uid=""):
        captured.update(
            {
                "sql": sql,
                "org_id": org_id,
                "facility_id": facility_id,
                "uid": uid,
            }
        )
        return {
            "columns": ["total"],
            "rows": [{"total": 1}],
            "row_count": 1,
            "truncated": False,
            "scope_applied": {"org_id": org_id},
        }

    monkeypatch.setattr("app.mcp.tools.wms_execute_analytical_query", fake_query)
    tool_executor._TOOL_REGISTRY = None

    try:
        result = asyncio.run(
            tool_executor.execute_tool(
                "wms_execute_analytical_query",
                {"sql": "SELECT COUNT(*) AS total FROM app_transaction"},
                uid="firebase-user-1",
                org_id="testorg",
                facility_id="FAC-001",
            )
        )
    finally:
        tool_executor._TOOL_REGISTRY = None

    assert captured["uid"] == "firebase-user-1"
    assert captured["org_id"] == "testorg"
    assert captured["facility_id"] == "FAC-001"
    assert result["row_count"] == 1


def test_mcp_server_lists_and_dispatches_analytics_tools(monkeypatch):
    tool_names = {tool.name for tool in asyncio.run(mcp_server.handle_list_tools())}
    assert {"wms_describe_schema", "wms_execute_analytical_query"} <= tool_names

    async def fake_describe_schema(**kwargs):
        return {"table_count": 1, "tables": [{"table_name": "app_transaction"}]}

    monkeypatch.setattr("app.mcp.tools.wms_describe_schema", fake_describe_schema)
    token = mcp_server._current_uid.set("firebase-user-1")

    try:
        response = asyncio.run(
            mcp_server.handle_call_tool(
                "wms_describe_schema",
                {"org_id": "testorg"},
            )
        )
    finally:
        mcp_server._current_uid.reset(token)

    payload = json.loads(response[0].text)
    assert payload["table_count"] == 1
    assert payload["tables"][0]["table_name"] == "app_transaction"
