"""Execute LLM tool calls by dispatching to app/mcp/tools.py functions."""
from __future__ import annotations

import json
import logging
from typing import Any

from app.ai.tool_definitions import MUTATION_TOOLS

logger = logging.getLogger(__name__)

# Map of tool name -> async function in app.mcp.tools
_TOOL_REGISTRY: dict[str, Any] | None = None


def _get_registry() -> dict[str, Any]:
    global _TOOL_REGISTRY
    if _TOOL_REGISTRY is None:
        from app.mcp import tools
        _TOOL_REGISTRY = {
            "wms_list_organizations": tools.wms_list_organizations,
            "wms_list_facilities": tools.wms_list_facilities,
            "wms_list_skus": tools.wms_list_skus,
            "wms_list_zones": tools.wms_list_zones,
            "wms_list_locations": tools.wms_list_locations,
            "wms_get_inventory_balances": tools.wms_get_inventory_balances,
            "wms_get_inventory_ledger": tools.wms_get_inventory_ledger,
            "wms_list_transactions": tools.wms_list_transactions,
            "wms_get_transaction": tools.wms_get_transaction,
            "wms_create_transaction": tools.wms_create_transaction,
            "wms_execute_transaction": tools.wms_execute_transaction,
            "wms_cancel_transaction": tools.wms_cancel_transaction,
            "wms_move_inventory": tools.wms_move_inventory,
            "wms_create_grn": tools.wms_create_grn,
            "wms_putaway": tools.wms_putaway,
            "wms_order_pick": tools.wms_order_pick,
            "wms_semantic_search": tools.wms_semantic_search,
        }
    return _TOOL_REGISTRY


def is_mutation_tool(tool_name: str) -> bool:
    """Return True if the tool modifies data and requires confirmation."""
    return tool_name in MUTATION_TOOLS


async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    uid: str,
    org_id: str,
    facility_id: str | None = None,
) -> dict[str, Any]:
    """Execute a WMS tool, auto-injecting org_id, facility_id, and uid.

    Returns the tool result as a dict.
    Raises KeyError for unknown tools.
    """
    registry = _get_registry()
    func = registry.get(tool_name)
    if func is None:
        raise KeyError(f"Unknown tool: {tool_name}")

    # Auto-inject session context
    args = dict(arguments)
    args["uid"] = uid
    args["org_id"] = org_id
    if facility_id and "facility_id" in _get_tool_param_names(tool_name):
        args.setdefault("facility_id", facility_id)

    logger.info("Executing tool %s with args: %s", tool_name, {k: v for k, v in args.items() if k != "uid"})
    result = await func(**args)
    return result


def _get_tool_param_names(tool_name: str) -> set[str]:
    """Get the parameter names for a tool function via inspection."""
    import inspect
    registry = _get_registry()
    func = registry.get(tool_name)
    if func is None:
        return set()
    # Handle sync_to_async wrapped functions
    actual = getattr(func, "__wrapped__", func)
    sig = inspect.signature(actual)
    return set(sig.parameters.keys())


def summarize_result(result: Any, max_items: int = 10) -> str:
    """Create a summary of tool results for feeding back to the LLM.

    For large result sets, truncates to max_items and notes the total count.
    Full data goes to the frontend via components, but the LLM only sees the summary.
    """
    if isinstance(result, list):
        total = len(result)
        truncated = result[:max_items]
        summary = json.dumps(truncated, indent=2, default=str)
        if total > max_items:
            summary += f"\n\n... and {total - max_items} more items (total: {total})"
        return summary
    return json.dumps(result, indent=2, default=str)
