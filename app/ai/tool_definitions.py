"""Convert MCP tool definitions to OpenAI function-calling format for LLM providers."""
from __future__ import annotations

from app.mcp.server import _TOOL_DEFS

# Tools that modify data and require user confirmation before execution.
MUTATION_TOOLS = frozenset({
    "wms_create_grn",
    "wms_putaway",
    "wms_move_inventory",
    "wms_order_pick",
    "wms_create_transaction",
    "wms_execute_transaction",
    "wms_cancel_transaction",
})

# Parameters that are auto-injected from the user session context.
AUTO_INJECT_PARAMS = frozenset({"org_id", "facility_id"})


def get_openai_tools() -> list[dict]:
    """Return tool definitions in OpenAI function-calling format."""
    tools = []
    for tool_def in _TOOL_DEFS:
        schema = dict(tool_def.inputSchema)
        # Remove auto-injected params from the schema so the LLM doesn't need to provide them
        props = {k: v for k, v in schema.get("properties", {}).items() if k not in AUTO_INJECT_PARAMS}
        required = [r for r in schema.get("required", []) if r not in AUTO_INJECT_PARAMS]

        tools.append({
            "type": "function",
            "function": {
                "name": tool_def.name,
                "description": tool_def.description,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": required,
                },
            },
        })
    return tools


def get_anthropic_tools() -> list[dict]:
    """Return tool definitions in Anthropic/Claude format."""
    tools = []
    for tool_def in _TOOL_DEFS:
        schema = dict(tool_def.inputSchema)
        props = {k: v for k, v in schema.get("properties", {}).items() if k not in AUTO_INJECT_PARAMS}
        required = [r for r in schema.get("required", []) if r not in AUTO_INJECT_PARAMS]

        tools.append({
            "name": tool_def.name,
            "description": tool_def.description,
            "input_schema": {
                "type": "object",
                "properties": props,
                "required": required,
            },
        })
    return tools
