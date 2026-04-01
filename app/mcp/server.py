"""MCP server definition — tools, authentication, and SSE session handling."""
from __future__ import annotations

import asyncio
import contextvars
import json
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.auth.firebase_verifier import FirebaseInvalidTokenError, get_firebase_verifier

# Per-connection context: Firebase UID of the authenticated user
_current_uid: contextvars.ContextVar[str] = contextvars.ContextVar("mcp_uid", default="")

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp_server = Server("yes-wms")

_TOOL_DEFS: list[types.Tool] = [
    types.Tool(
        name="wms_list_organizations",
        description="List all organizations in the YES WMS.",
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="wms_list_facilities",
        description="List all facilities/warehouses for an organization.",
        inputSchema={
            "type": "object",
            "properties": {"org_id": {"type": "string", "description": "Organization ID"}},
            "required": ["org_id"],
        },
    ),
    types.Tool(
        name="wms_list_skus",
        description="List all SKUs (products) registered for an organization.",
        inputSchema={
            "type": "object",
            "properties": {"org_id": {"type": "string"}},
            "required": ["org_id"],
        },
    ),
    types.Tool(
        name="wms_list_zones",
        description="List all storage zones for an organization.",
        inputSchema={
            "type": "object",
            "properties": {"org_id": {"type": "string"}},
            "required": ["org_id"],
        },
    ),
    types.Tool(
        name="wms_list_locations",
        description="List all bin/shelf locations for an organization.",
        inputSchema={
            "type": "object",
            "properties": {"org_id": {"type": "string"}},
            "required": ["org_id"],
        },
    ),
    types.Tool(
        name="wms_get_inventory_balances",
        description=(
            "Query current stock levels. Filter by facility, SKU, entity type, or entity code. "
            "Returns on-hand, reserved, and available quantities."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "facility_id": {"type": "string", "description": "Facility code (optional)"},
                "sku_code": {"type": "string", "description": "Filter by SKU code"},
                "entity_type": {"type": "string", "description": "LOCATION, ZONE, INVOICE, etc."},
                "entity_code": {"type": "string", "description": "Specific entity code"},
            },
            "required": ["org_id"],
        },
    ),
    types.Tool(
        name="wms_get_inventory_ledger",
        description="Query inventory ledger — full transaction history with signed quantities.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "facility_id": {"type": "string"},
                "sku_code": {"type": "string"},
                "transaction_id": {"type": "string", "format": "uuid"},
            },
            "required": ["org_id"],
        },
    ),
    types.Tool(
        name="wms_list_transactions",
        description="List warehouse transactions with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "facility_id": {"type": "string"},
                "transaction_type": {
                    "type": "string",
                    "enum": ["MOVE", "ORDER_PICK", "GRN", "PUTAWAY", "RETURN", "CYCLE_COUNT", "ADJUSTMENT"],
                },
                "status": {
                    "type": "string",
                    "enum": ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED", "PARTIALLY_COMPLETED"],
                },
                "date_from": {
                    "type": "string",
                    "description": "Filter transactions created on or after this ISO date/datetime (e.g. 2025-01-15 or 2025-01-15T00:00:00Z)",
                },
                "date_to": {
                    "type": "string",
                    "description": "Filter transactions created on or before this ISO date/datetime (e.g. 2025-01-15 or 2025-01-15T23:59:59Z)",
                },
            },
            "required": ["org_id"],
        },
    ),
    types.Tool(
        name="wms_get_transaction",
        description="Get a single transaction by ID with full picks and drops detail.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "transaction_id": {"type": "string", "format": "uuid"},
            },
            "required": ["org_id", "transaction_id"],
        },
    ),
    types.Tool(
        name="wms_create_transaction",
        description=(
            "Create a warehouse transaction in PENDING status. "
            "Use wms_execute_transaction to commit it to inventory."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "facility_id": {"type": "string"},
                "transaction_type": {
                    "type": "string",
                    "enum": ["MOVE", "ORDER_PICK", "GRN", "PUTAWAY", "RETURN", "CYCLE_COUNT", "ADJUSTMENT"],
                },
                "picks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sku_code": {"type": "string"},
                            "source_entity_type": {"type": "string", "default": "LOCATION"},
                            "source_entity_code": {"type": "string"},
                            "quantity": {"type": "string"},
                            "batch_number": {"type": "string", "default": ""},
                        },
                        "required": ["sku_code", "source_entity_code", "quantity"],
                    },
                },
                "drops": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sku_code": {"type": "string"},
                            "dest_entity_type": {"type": "string", "default": "LOCATION"},
                            "dest_entity_code": {"type": "string"},
                            "quantity": {"type": "string"},
                            "batch_number": {"type": "string", "default": ""},
                        },
                        "required": ["sku_code", "dest_entity_code", "quantity"],
                    },
                },
                "reference_number": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["org_id", "facility_id", "transaction_type", "picks", "drops"],
        },
    ),
    types.Tool(
        name="wms_execute_transaction",
        description="Execute a PENDING transaction — debits picks and credits drops atomically.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "transaction_id": {"type": "string", "format": "uuid"},
            },
            "required": ["org_id", "transaction_id"],
        },
    ),
    types.Tool(
        name="wms_cancel_transaction",
        description="Cancel a PENDING or IN_PROGRESS transaction.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "transaction_id": {"type": "string", "format": "uuid"},
            },
            "required": ["org_id", "transaction_id"],
        },
    ),
    types.Tool(
        name="wms_move_inventory",
        description="Move stock between two locations (creates and executes a MOVE transaction).",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "facility_id": {"type": "string"},
                "sku_code": {"type": "string"},
                "source_entity_code": {"type": "string"},
                "dest_entity_code": {"type": "string"},
                "quantity": {"type": "string", "description": "Decimal string, e.g. \"10\" or \"2.5\""},
                "source_entity_type": {"type": "string", "default": "LOCATION"},
                "dest_entity_type": {"type": "string", "default": "LOCATION"},
                "batch_number": {"type": "string", "default": ""},
                "reference_number": {"type": "string"},
            },
            "required": ["org_id", "facility_id", "sku_code", "source_entity_code", "dest_entity_code", "quantity"],
        },
    ),
    types.Tool(
        name="wms_create_grn",
        description=(
            "Goods Received Note — receive items into the PRE_PUTAWAY staging zone "
            "(creates and executes a GRN transaction)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "facility_id": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sku_code": {"type": "string"},
                            "quantity": {"type": "string"},
                            "dest_entity_code": {"type": "string", "default": "PRE_PUTAWAY"},
                            "dest_entity_type": {"type": "string", "default": "ZONE"},
                            "batch_number": {"type": "string", "default": ""},
                        },
                        "required": ["sku_code", "quantity"],
                    },
                },
                "reference_number": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["org_id", "facility_id", "items"],
        },
    ),
    types.Tool(
        name="wms_putaway",
        description="Move inventory from PRE_PUTAWAY staging zone to a storage location.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "facility_id": {"type": "string"},
                "sku_code": {"type": "string"},
                "dest_entity_code": {"type": "string", "description": "Destination storage location code"},
                "quantity": {"type": "string"},
                "source_entity_code": {"type": "string", "default": "PRE_PUTAWAY"},
                "source_entity_type": {"type": "string", "default": "ZONE"},
                "dest_entity_type": {"type": "string", "default": "LOCATION"},
                "batch_number": {"type": "string", "default": ""},
                "reference_number": {"type": "string"},
            },
            "required": ["org_id", "facility_id", "sku_code", "dest_entity_code", "quantity"],
        },
    ),
    types.Tool(
        name="wms_order_pick",
        description="Pick inventory from a location for an order or invoice.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "facility_id": {"type": "string"},
                "sku_code": {"type": "string"},
                "source_entity_code": {"type": "string", "description": "Source location code"},
                "dest_entity_code": {"type": "string", "description": "Invoice/order reference code"},
                "quantity": {"type": "string"},
                "source_entity_type": {"type": "string", "default": "LOCATION"},
                "dest_entity_type": {"type": "string", "default": "INVOICE"},
                "batch_number": {"type": "string", "default": ""},
                "reference_number": {"type": "string"},
            },
            "required": ["org_id", "facility_id", "sku_code", "source_entity_code", "dest_entity_code", "quantity"],
        },
    ),
    types.Tool(
        name="wms_semantic_search",
        description=(
            "Semantic similarity search over warehouse data — transactions, SKUs, past conversations, "
            "and the knowledge base (SOPs / procedures). Use when the user asks about historical patterns, "
            "wants to find records by natural language description, searches for a product by name or "
            "description (not exact code), or asks procedural questions about warehouse operations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "query": {
                    "type": "string",
                    "description": "Natural language search query, e.g. 'GRNs with damaged items' or 'putaway procedure'",
                },
                "content_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["transaction", "sku", "message", "knowledge"],
                    },
                    "description": "Which data sources to search. Omit to search all sources.",
                },
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum number of results to return (1–10).",
                },
            },
            "required": ["org_id", "query"],
        },
    ),
]


@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return _TOOL_DEFS


@mcp_server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    from app.core.exceptions import AppError
    from app.mcp import tools

    args: dict[str, Any] = arguments or {}
    uid = _current_uid.get()

    def _json(data: Any) -> list[types.TextContent]:
        return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

    def _err(msg: str) -> list[types.TextContent]:
        return [types.TextContent(type="text", text=msg)]

    try:
        if name == "wms_list_organizations":
            result = await tools.wms_list_organizations(uid=uid)
        elif name == "wms_list_facilities":
            result = await tools.wms_list_facilities(**args, uid=uid)
        elif name == "wms_list_skus":
            result = await tools.wms_list_skus(**args, uid=uid)
        elif name == "wms_list_zones":
            result = await tools.wms_list_zones(**args, uid=uid)
        elif name == "wms_list_locations":
            result = await tools.wms_list_locations(**args, uid=uid)
        elif name == "wms_get_inventory_balances":
            result = await tools.wms_get_inventory_balances(**args, uid=uid)
        elif name == "wms_get_inventory_ledger":
            result = await tools.wms_get_inventory_ledger(**args, uid=uid)
        elif name == "wms_list_transactions":
            result = await tools.wms_list_transactions(**args, uid=uid)
        elif name == "wms_get_transaction":
            result = await tools.wms_get_transaction(**args, uid=uid)
        elif name == "wms_create_transaction":
            result = await tools.wms_create_transaction(**args, uid=uid)
        elif name == "wms_execute_transaction":
            result = await tools.wms_execute_transaction(**args, uid=uid)
        elif name == "wms_cancel_transaction":
            result = await tools.wms_cancel_transaction(**args, uid=uid)
        elif name == "wms_move_inventory":
            result = await tools.wms_move_inventory(**args, uid=uid)
        elif name == "wms_create_grn":
            result = await tools.wms_create_grn(**args, uid=uid)
        elif name == "wms_putaway":
            result = await tools.wms_putaway(**args, uid=uid)
        elif name == "wms_order_pick":
            result = await tools.wms_order_pick(**args, uid=uid)
        elif name == "wms_semantic_search":
            result = await tools.wms_semantic_search(**args, uid=uid)
        else:
            return _err(f"Unknown tool: {name}")

        return _json(result)

    except AppError as exc:
        return _err(f"WMS error [{exc.code}]: {exc.message}")
    except Exception as exc:
        return _err(f"Error: {exc!s}")


# ---------------------------------------------------------------------------
# SSE transport + request handlers
# ---------------------------------------------------------------------------

sse_transport = SseServerTransport("/mcp/messages")


async def handle_sse(request: Request) -> Response:
    """GET /mcp/sse — authenticate via Bearer token then open SSE session."""
    auth_header = request.headers.get("authorization", "")
    token = ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()

    if not token:
        return JSONResponse({"error": "missing_token"}, status_code=401)

    try:
        claims = await asyncio.to_thread(get_firebase_verifier().verify, token)
    except FirebaseInvalidTokenError:
        return JSONResponse({"error": "invalid_token"}, status_code=401)
    except Exception:
        return JSONResponse({"error": "verification_failed"}, status_code=500)

    uid_token = _current_uid.set(claims.get("uid", ""))
    try:
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(),
            )
    finally:
        _current_uid.reset(uid_token)

    return Response()


async def handle_messages(request: Request) -> Response:
    """POST /mcp/messages — relay client messages to the SSE session."""
    await sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )
    return Response()
