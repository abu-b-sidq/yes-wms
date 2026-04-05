"""Read-only analytics helpers for YES WMS MCP tools."""
from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db import connection, models

from app.core.exceptions import ValidationError
from app.inventory.models import InventoryBalance, InventoryLedger
from app.masters.models import (
    Facility,
    FacilityLocation,
    FacilitySKU,
    FacilityZone,
    Location,
    Organization,
    SKU,
    Zone,
)
from app.operations.models import Drop, Pick, PurchaseOrder, SaleOrder, Transaction

ANALYTICS_MODELS = (
    Organization,
    Facility,
    SKU,
    Zone,
    Location,
    FacilitySKU,
    FacilityZone,
    FacilityLocation,
    PurchaseOrder,
    SaleOrder,
    Transaction,
    Pick,
    Drop,
    InventoryBalance,
    InventoryLedger,
)

ANALYTICS_MODELS_BY_TABLE = {model._meta.db_table: model for model in ANALYTICS_MODELS}
ANALYTICS_ALLOWED_TABLES = frozenset(ANALYTICS_MODELS_BY_TABLE.keys())

MAX_ANALYTICS_LIMIT = 500
DEFAULT_ANALYTICS_LIMIT = 200
_RESULT_SAMPLE_ROWS = 10

_COMMENT_PATTERN = re.compile(r"(--|/\*|\*/)")
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|truncate|grant|revoke|create|replace|merge|"
    r"call|execute|vacuum|analyze|comment|copy|refresh|set|reset|show|pragma|attach|"
    r"detach|begin|commit|rollback"
    r")\b",
    re.IGNORECASE,
)
_RELATION_PATTERN = re.compile(
    r"""
    \b(?:from|join)\b
    \s+
    (?P<relation>
        "(?:[^"]+)"
        |
        [a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)?
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

_TABLE_METADATA: dict[str, dict[str, Any]] = {
    "app_organization": {
        "domain": "masters",
        "business_description": "Top-level tenant boundary for all warehouse data.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": False,
            "scope_columns": ["id"],
        },
        "join_hints": [
            "Join app_facility.org_id to app_organization.id to list warehouses in the active organization.",
            "Join app_transaction.org_id to app_organization.id to summarize warehouse activity by tenant.",
        ],
    },
    "app_facility": {
        "domain": "masters",
        "business_description": "Warehouse or facility master records for the active organization.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["org_id", "code"],
        },
        "join_hints": [
            "Join app_transaction.facility_id to app_facility.id for transaction activity by warehouse.",
            "Join app_inventory_balance.facility_id to app_facility.id for stock by warehouse.",
        ],
    },
    "app_sku": {
        "domain": "masters",
        "business_description": "Product catalog entries used by inventory and operations.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": False,
            "scope_columns": ["org_id"],
        },
        "join_hints": [
            "Join app_inventory_balance.sku_id to app_sku.id for stock by SKU.",
            "Join app_pick.sku_id or app_drop.sku_id to app_sku.id for movement analytics.",
        ],
    },
    "app_zone": {
        "domain": "masters",
        "business_description": "Logical storage zones defined within the organization.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": False,
            "scope_columns": ["org_id"],
        },
        "join_hints": [
            "Join app_location.zone_id to app_zone.id to group bins by zone.",
            "Join app_facility_zone.zone_id to app_zone.id to see which zones are active in a facility.",
        ],
    },
    "app_location": {
        "domain": "masters",
        "business_description": "Storage bins or shelves that can hold inventory.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": False,
            "scope_columns": ["org_id"],
        },
        "join_hints": [
            "Join app_location.zone_id to app_zone.id to report locations by zone.",
            "Join app_inventory_balance.entity_code to app_location.code when entity_type = 'LOCATION'.",
        ],
    },
    "app_facility_sku": {
        "domain": "masters",
        "business_description": "Facility-specific SKU activation and override mapping.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["facility_id"],
        },
        "join_hints": [
            "Join app_facility_sku.facility_id to app_facility.id for warehouse-specific catalog availability.",
            "Join app_facility_sku.sku_id to app_sku.id to inspect active SKU overrides per warehouse.",
        ],
    },
    "app_facility_zone": {
        "domain": "masters",
        "business_description": "Facility-specific zone activation and override mapping.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["facility_id"],
        },
        "join_hints": [
            "Join app_facility_zone.facility_id to app_facility.id for warehouse-zone coverage.",
            "Join app_facility_zone.zone_id to app_zone.id to inspect active zone overrides per facility.",
        ],
    },
    "app_facility_location": {
        "domain": "masters",
        "business_description": "Facility-specific location activation and override mapping.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["facility_id"],
        },
        "join_hints": [
            "Join app_facility_location.facility_id to app_facility.id for warehouse-specific bin coverage.",
            "Join app_facility_location.location_id to app_location.id to inspect active location overrides per facility.",
        ],
    },
    "app_purchase_order": {
        "domain": "operations",
        "business_description": "Inbound purchase orders that feed receiving and GRN activity.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["org_id", "facility_id"],
        },
        "join_hints": [
            "Join app_purchase_order.facility_id to app_facility.id for inbound workload by warehouse.",
            "Join app_transaction.purchase_order_id to app_purchase_order.id to connect receipts to POs.",
        ],
    },
    "app_sale_order": {
        "domain": "operations",
        "business_description": "Outbound sales orders that feed picking and dispatch work.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["org_id", "facility_id"],
        },
        "join_hints": [
            "Join app_sale_order.facility_id to app_facility.id for outbound workload by warehouse.",
            "Join app_transaction.sale_order_id to app_sale_order.id to connect picks to customer orders.",
        ],
    },
    "app_transaction": {
        "domain": "operations",
        "business_description": "Core warehouse transactions such as GRN, putaway, move, and order pick.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["org_id", "facility_id"],
        },
        "join_hints": [
            "Join app_transaction.facility_id to app_facility.id for warehouse activity trends.",
            "Join app_pick.transaction_id or app_drop.transaction_id to app_transaction.id for line-level execution detail.",
            "Join app_inventory_ledger.transaction_id to app_transaction.id for audit-trail analytics.",
        ],
    },
    "app_pick": {
        "domain": "operations",
        "business_description": "Pick task lines attached to warehouse transactions.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["org_id", "transaction_id (via app_transaction.facility_id)"],
        },
        "join_hints": [
            "Join app_pick.transaction_id to app_transaction.id for pick workload by transaction type or status.",
            "Join app_pick.sku_id to app_sku.id for SKU-level outbound movement analytics.",
        ],
    },
    "app_drop": {
        "domain": "operations",
        "business_description": "Drop task lines attached to warehouse transactions.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["org_id", "transaction_id (via app_transaction.facility_id)"],
        },
        "join_hints": [
            "Join app_drop.transaction_id to app_transaction.id for drop workload by transaction type or status.",
            "Join app_drop.sku_id to app_sku.id for SKU-level receiving and putaway analytics.",
        ],
    },
    "app_inventory_balance": {
        "domain": "inventory",
        "business_description": "Current stock balance snapshot by SKU, facility, entity, and batch.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["org_id", "facility_id"],
        },
        "join_hints": [
            "Join app_inventory_balance.sku_id to app_sku.id for current stock by product.",
            "Join app_inventory_balance.facility_id to app_facility.id for warehouse stock summaries.",
            "Join app_inventory_balance.entity_code to app_location.code when entity_type = 'LOCATION' for location stock views.",
        ],
    },
    "app_inventory_ledger": {
        "domain": "inventory",
        "business_description": "Immutable inventory movement history with signed quantities and post-entry balances.",
        "scope": {
            "org_scoped": True,
            "facility_scoped": True,
            "scope_columns": ["org_id", "facility_id"],
        },
        "join_hints": [
            "Join app_inventory_ledger.transaction_id to app_transaction.id for full movement audit trails.",
            "Join app_inventory_ledger.sku_id to app_sku.id for SKU movement velocity and traceability.",
            "Join app_inventory_ledger.facility_id to app_facility.id for warehouse-level ledger summaries.",
        ],
    },
}


def describe_schema(table_names: list[str] | None = None) -> dict[str, Any]:
    """Return a curated schema catalog for analytics-safe warehouse tables."""
    selected_tables = _normalize_requested_tables(table_names)
    tables = [build_table_schema(table_name) for table_name in selected_tables]
    return {
        "table_count": len(tables),
        "tables": tables,
    }


def build_table_schema(table_name: str) -> dict[str, Any]:
    model = _get_model_for_table(table_name)
    meta = _TABLE_METADATA[table_name]
    return {
        "table_name": table_name,
        "model_name": model._meta.label,
        "domain": meta["domain"],
        "business_description": meta["business_description"],
        "scope": meta["scope"],
        "primary_key": {
            "name": model._meta.pk.name,
            "column": model._meta.pk.column,
            "type": model._meta.pk.db_type(connection),
        },
        "columns": _build_columns(model),
        "foreign_keys": _build_foreign_keys(model),
        "indexes": _build_indexes(model),
        "join_hints": meta["join_hints"][:3],
    }


def execute_analytical_query(
    *,
    sql: str,
    org_id: str,
    facility_code: str | None = None,
    facility_pk: str | None = None,
    limit: int = DEFAULT_ANALYTICS_LIMIT,
) -> dict[str, Any]:
    """Validate, scope, and execute a guarded analytical query."""
    normalized_limit = _normalize_limit(limit)
    validation = validate_analytical_sql(sql)
    final_sql, params, scope_applied = build_scoped_query(
        sql=sql,
        org_id=org_id,
        facility_code=facility_code,
        facility_pk=facility_pk,
        limit=normalized_limit,
        referenced_allowed_tables=validation["allowed_tables"],
    )

    with connection.cursor() as cursor:
        cursor.execute(final_sql, params)
        raw_rows = cursor.fetchall()
        description = cursor.description or []

    columns = _unique_column_names([col[0] for col in description])
    rows = [
        _to_json_safe(dict(zip(columns, row)))
        for row in raw_rows[:normalized_limit]
    ]
    truncated = len(raw_rows) > normalized_limit
    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "scope_applied": scope_applied,
    }


def validate_analytical_sql(sql: str) -> dict[str, Any]:
    """Validate that the query is a single read-only SELECT over allowed tables."""
    normalized = sql.strip()
    if not normalized:
        raise ValidationError("Analytical SQL cannot be blank.")
    if _COMMENT_PATTERN.search(normalized):
        raise ValidationError("SQL comments are not allowed in analytical queries.")
    if ";" in normalized:
        raise ValidationError("Semicolons are not allowed in analytical queries.")

    lowered = normalized.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValidationError("Analytical queries must start with SELECT or WITH.")
    if _FORBIDDEN_KEYWORDS.search(normalized):
        raise ValidationError("Only read-only SELECT queries are allowed.")

    cte_names = extract_cte_names(normalized)
    referenced_relations = extract_relation_names(normalized)
    if not referenced_relations:
        raise ValidationError("Analytical queries must reference at least one allowed table.")

    disallowed: list[str] = []
    allowed_tables: set[str] = set()
    for relation in referenced_relations:
        if "." in relation:
            raise ValidationError("Schema-qualified table references are not allowed.")
        if relation in cte_names:
            continue
        if relation not in ANALYTICS_ALLOWED_TABLES:
            disallowed.append(relation)
            continue
        allowed_tables.add(relation)

    if disallowed:
        raise ValidationError(
            f"Analytical query references disallowed relations: {', '.join(sorted(set(disallowed)))}."
        )
    if not allowed_tables:
        raise ValidationError("Analytical queries must read from at least one allowed warehouse table.")

    return {
        "cte_names": sorted(cte_names),
        "relations": sorted(referenced_relations),
        "allowed_tables": sorted(allowed_tables),
    }


def extract_relation_names(sql: str) -> set[str]:
    """Extract table-like relations mentioned in FROM/JOIN clauses."""
    cleaned_sql = _strip_string_literals(sql)
    relations: set[str] = set()
    for match in _RELATION_PATTERN.finditer(cleaned_sql):
        relation = match.group("relation").strip()
        if relation.startswith('"') and relation.endswith('"'):
            relation = relation[1:-1]
        relations.add(relation)
    return relations


def extract_cte_names(sql: str) -> set[str]:
    """Extract top-level CTE names from a WITH query."""
    text = sql.lstrip()
    if not text.lower().startswith("with"):
        return set()

    index = 4
    index = _skip_whitespace(text, index)
    if text[index:index + 9].lower() == "recursive":
        index += 9

    cte_names: set[str] = set()
    while index < len(text):
        index = _skip_whitespace(text, index)
        name, index = _consume_identifier(text, index)
        cte_names.add(name)

        index = _skip_whitespace(text, index)
        if index < len(text) and text[index] == "(":
            index = _consume_parenthesized(text, index)
            index = _skip_whitespace(text, index)

        if text[index:index + 2].lower() != "as":
            raise ValidationError("Unable to parse WITH query structure.")
        index += 2
        index = _skip_whitespace(text, index)
        if index >= len(text) or text[index] != "(":
            raise ValidationError("Unable to parse WITH query structure.")
        index = _consume_parenthesized(text, index)
        index = _skip_whitespace(text, index)

        if index < len(text) and text[index] == ",":
            index += 1
            continue
        break

    return cte_names


def build_scoped_query(
    *,
    sql: str,
    org_id: str,
    facility_code: str | None,
    facility_pk: str | None,
    limit: int,
    referenced_allowed_tables: list[str] | None = None,
) -> tuple[str, list[Any], dict[str, Any]]:
    """Wrap user SQL with scoped CTEs for the allowed warehouse tables."""
    selected_tables = referenced_allowed_tables or sorted(ANALYTICS_ALLOWED_TABLES)
    cte_sql_parts: list[str] = []
    params: list[Any] = []
    facility_scoped_tables: list[str] = []

    for table_name in selected_tables:
        table_sql, table_params, is_facility_scoped = _build_table_scope_cte(
            table_name,
            org_id=org_id,
            facility_code=facility_code,
            facility_pk=facility_pk,
        )
        cte_sql_parts.append(f"{table_name} AS ({table_sql})")
        params.extend(table_params)
        if is_facility_scoped:
            facility_scoped_tables.append(table_name)

    params.append(limit + 1)
    wrapped_sql = (
        "WITH "
        + ", ".join(cte_sql_parts)
        + ", __wms_user_query AS ("
        + sql.strip()
        + ") "
        + "SELECT * FROM __wms_user_query LIMIT %s"
    )

    scope_applied = {
        "org_id": org_id,
        "facility_code": facility_code,
        "facility_pk": facility_pk,
        "scoped_tables": selected_tables,
        "facility_scoped_tables": sorted(facility_scoped_tables),
    }
    return wrapped_sql, params, scope_applied


def _normalize_requested_tables(table_names: list[str] | None) -> list[str]:
    if not table_names:
        return sorted(ANALYTICS_ALLOWED_TABLES)

    normalized: list[str] = []
    seen: set[str] = set()
    for table_name in table_names:
        candidate = table_name.strip()
        if not candidate:
            continue
        if candidate not in ANALYTICS_ALLOWED_TABLES:
            raise ValidationError(f"Unsupported analytics table: {candidate}.")
        if candidate not in seen:
            normalized.append(candidate)
            seen.add(candidate)

    if not normalized:
        raise ValidationError("At least one supported analytics table must be requested.")
    return normalized


def _get_model_for_table(table_name: str):
    model = ANALYTICS_MODELS_BY_TABLE.get(table_name)
    if model is None:
        raise ValidationError(f"Unsupported analytics table: {table_name}.")
    return model


def _build_columns(model) -> list[dict[str, Any]]:
    columns: list[dict[str, Any]] = []
    for field in model._meta.concrete_fields:
        columns.append(
            {
                "name": field.name,
                "column": field.column,
                "type": field.db_type(connection),
                "nullable": field.null,
                "primary_key": field.primary_key,
                "foreign_key": bool(getattr(field, "remote_field", None)),
            }
        )
    return columns


def _build_foreign_keys(model) -> list[dict[str, Any]]:
    foreign_keys: list[dict[str, Any]] = []
    for field in model._meta.concrete_fields:
        remote_field = getattr(field, "remote_field", None)
        if not remote_field or not getattr(remote_field, "model", None):
            continue
        remote_model = remote_field.model
        foreign_keys.append(
            {
                "name": field.name,
                "column": field.column,
                "references_table": remote_model._meta.db_table,
                "references_model": remote_model._meta.label,
                "references_column": remote_model._meta.pk.column,
            }
        )
    return foreign_keys


def _build_indexes(model) -> list[dict[str, Any]]:
    indexes: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[str, ...], bool]] = set()

    for field in model._meta.concrete_fields:
        if field.primary_key or not (field.db_index or field.unique):
            continue
        descriptor = (field.column, (field.column,), bool(field.unique))
        if descriptor in seen:
            continue
        seen.add(descriptor)
        indexes.append(
            {
                "name": f"{model._meta.db_table}_{field.column}_idx",
                "columns": [field.column],
                "unique": bool(field.unique),
                "source": "field",
            }
        )

    for index in model._meta.indexes:
        columns = tuple(_field_name_to_column(model, field_name) for field_name in index.fields)
        descriptor = (index.name, columns, False)
        if descriptor in seen:
            continue
        seen.add(descriptor)
        indexes.append(
            {
                "name": index.name,
                "columns": list(columns),
                "unique": False,
                "source": "meta",
            }
        )

    for constraint in model._meta.constraints:
        if not isinstance(constraint, models.UniqueConstraint):
            continue
        columns = tuple(_field_name_to_column(model, field_name) for field_name in constraint.fields)
        descriptor = (constraint.name, columns, True)
        if descriptor in seen:
            continue
        seen.add(descriptor)
        indexes.append(
            {
                "name": constraint.name,
                "columns": list(columns),
                "unique": True,
                "source": "constraint",
            }
        )

    return indexes


def _normalize_limit(limit: int) -> int:
    if limit <= 0:
        raise ValidationError("Analytical query limit must be greater than zero.")
    if limit > MAX_ANALYTICS_LIMIT:
        raise ValidationError(
            f"Analytical query limit cannot exceed {MAX_ANALYTICS_LIMIT} rows."
        )
    return limit


def _field_name_to_column(model, field_name: str) -> str:
    return model._meta.get_field(field_name).column


def _build_table_scope_cte(
    table_name: str,
    *,
    org_id: str,
    facility_code: str | None,
    facility_pk: str | None,
) -> tuple[str, list[Any], bool]:
    if table_name == "app_organization":
        return (
            'SELECT * FROM "app_organization" WHERE id = %s',
            [org_id],
            False,
        )

    if table_name == "app_facility":
        sql = 'SELECT * FROM "app_facility" WHERE org_id = %s'
        params: list[Any] = [org_id]
        if facility_code:
            sql += " AND code = %s"
            params.append(facility_code)
        return sql, params, bool(facility_code)

    if table_name in {"app_sku", "app_zone", "app_location"}:
        return (
            f'SELECT * FROM "{table_name}" WHERE org_id = %s',
            [org_id],
            False,
        )

    if table_name in {"app_purchase_order", "app_sale_order", "app_transaction", "app_inventory_balance", "app_inventory_ledger"}:
        sql = f'SELECT * FROM "{table_name}" WHERE org_id = %s'
        params = [org_id]
        if facility_pk:
            sql += " AND facility_id = %s"
            params.append(facility_pk)
        return sql, params, bool(facility_pk)

    if table_name in {"app_facility_sku", "app_facility_zone", "app_facility_location"}:
        facility_filter_sql, facility_params = _build_facility_scope_subquery(
            org_id=org_id,
            facility_code=facility_code,
        )
        return (
            f'SELECT * FROM "{table_name}" WHERE facility_id IN ({facility_filter_sql})',
            facility_params,
            bool(facility_code),
        )

    if table_name in {"app_pick", "app_drop"}:
        transaction_scope_sql, transaction_params = _build_transaction_scope_subquery(
            org_id=org_id,
            facility_pk=facility_pk,
        )
        return (
            f'SELECT * FROM "{table_name}" WHERE org_id = %s AND transaction_id IN ({transaction_scope_sql})',
            [org_id, *transaction_params],
            bool(facility_pk),
        )

    raise ValidationError(f"Unsupported analytics table: {table_name}.")


def _build_facility_scope_subquery(
    *,
    org_id: str,
    facility_code: str | None,
) -> tuple[str, list[Any]]:
    sql = 'SELECT id FROM "app_facility" WHERE org_id = %s'
    params: list[Any] = [org_id]
    if facility_code:
        sql += " AND code = %s"
        params.append(facility_code)
    return sql, params


def _build_transaction_scope_subquery(
    *,
    org_id: str,
    facility_pk: str | None,
) -> tuple[str, list[Any]]:
    sql = 'SELECT id FROM "app_transaction" WHERE org_id = %s'
    params: list[Any] = [org_id]
    if facility_pk:
        sql += " AND facility_id = %s"
        params.append(facility_pk)
    return sql, params


def _strip_string_literals(sql: str) -> str:
    pieces: list[str] = []
    in_single = False
    in_double = False
    index = 0
    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""
        if in_single:
            if char == "'" and next_char == "'":
                index += 2
                continue
            if char == "'":
                in_single = False
            index += 1
            continue
        if in_double:
            pieces.append(char)
            if char == '"':
                in_double = False
            index += 1
            continue
        if char == "'":
            in_single = True
            index += 1
            continue
        if char == '"':
            in_double = True
            pieces.append(char)
            index += 1
            continue
        pieces.append(char)
        index += 1
    return "".join(pieces)


def _skip_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _consume_identifier(text: str, index: int) -> tuple[str, int]:
    if index >= len(text):
        raise ValidationError("Unable to parse WITH query structure.")
    if text[index] == '"':
        end = text.find('"', index + 1)
        if end == -1:
            raise ValidationError("Unable to parse quoted identifier in WITH query.")
        return text[index + 1:end], end + 1

    match = re.match(r"[A-Za-z_][A-Za-z0-9_]*", text[index:])
    if not match:
        raise ValidationError("Unable to parse CTE name in WITH query.")
    return match.group(0), index + match.end()


def _consume_parenthesized(text: str, index: int) -> int:
    depth = 0
    in_single = False
    in_double = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_single:
            if char == "'" and next_char == "'":
                index += 2
                continue
            if char == "'":
                in_single = False
            index += 1
            continue

        if in_double:
            if char == '"':
                in_double = False
            index += 1
            continue

        if char == "'":
            in_single = True
            index += 1
            continue
        if char == '"':
            in_double = True
            index += 1
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1

    raise ValidationError("Unable to parse parenthesized SQL block.")


def _unique_column_names(columns: list[str]) -> list[str]:
    counts: Counter[str] = Counter()
    unique_columns: list[str] = []
    for column in columns:
        counts[column] += 1
        if counts[column] == 1:
            unique_columns.append(column)
        else:
            unique_columns.append(f"{column}_{counts[column]}")
    return unique_columns


def summarize_analytics_result(result: dict[str, Any], max_rows: int = _RESULT_SAMPLE_ROWS) -> dict[str, Any]:
    """Trim analytics payloads before they are sent back into the LLM context."""
    summarized = dict(result)
    if isinstance(result.get("rows"), list) and len(result["rows"]) > max_rows:
        summarized["rows"] = result["rows"][:max_rows]
        summarized["summary_note"] = (
            f"Showing the first {max_rows} rows in the tool summary. "
            "Use row_count and truncated for the full result shape."
        )
    if isinstance(result.get("tables"), list) and len(result["tables"]) > max_rows:
        summarized["tables"] = result["tables"][:max_rows]
        summarized["summary_note"] = (
            f"Showing the first {max_rows} tables in the tool summary. "
            "Use table_count for the full schema catalog."
        )
    return summarized


def _to_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, memoryview):
        return value.tobytes().hex()
    if isinstance(value, bytes):
        return value.hex()
    return value
