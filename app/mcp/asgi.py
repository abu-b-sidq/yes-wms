"""Starlette ASGI app for MCP — combines OAuth2 endpoints and SSE transport."""
from __future__ import annotations

from starlette.applications import Starlette
from starlette.routing import Route

from app.mcp.auth import (
    oauth_authorize,
    oauth_callback,
    oauth_metadata,
    oauth_register,
    oauth_token,
)
from app.mcp.server import handle_messages, handle_sse

mcp_starlette_app = Starlette(
    routes=[
        # OAuth2 discovery
        Route("/.well-known/oauth-authorization-server", oauth_metadata, methods=["GET"]),
        # OAuth2 endpoints
        Route("/mcp/oauth/authorize", oauth_authorize, methods=["GET"]),
        Route("/mcp/oauth/callback", oauth_callback, methods=["POST"]),
        Route("/mcp/oauth/token", oauth_token, methods=["POST"]),
        Route("/mcp/oauth/register", oauth_register, methods=["POST"]),
        # MCP SSE transport
        Route("/mcp/sse", handle_sse, methods=["GET"]),
        Route("/mcp/messages", handle_messages, methods=["POST"]),
    ],
)
