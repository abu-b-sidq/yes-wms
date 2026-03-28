import os

from dotenv import load_dotenv

# Load .env so FIREBASE_SERVICE_ACCOUNT_PATH etc. are available (e.g. when mounted in k8s at /app/.env)
if os.path.isfile("/app/.env"):
    load_dotenv("/app/.env")
else:
    load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wms_middleware.settings")

from django.core.asgi import get_asgi_application  # noqa: E402

# Calling get_asgi_application() triggers django.setup(), which must happen
# before any Django-dependent imports (mcp module, services, etc.).
_django_app = get_asgi_application()

# Import MCP Starlette app after Django is fully configured.
from app.mcp.asgi import mcp_starlette_app  # noqa: E402

_MCP_PREFIXES = ("/mcp", "/.well-known")


async def application(scope, receive, send):
    """ASGI entry point — routes MCP/OAuth traffic to Starlette, rest to Django."""
    if scope["type"] in ("http", "websocket"):
        path = scope.get("path", "")
        if any(path.startswith(p) for p in _MCP_PREFIXES):
            await mcp_starlette_app(scope, receive, send)
            return
    await _django_app(scope, receive, send)
