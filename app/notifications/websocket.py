from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

from starlette.websockets import WebSocket, WebSocketDisconnect

logger = logging.getLogger("app.notifications.websocket")

# In-memory connection registries
# user_id -> set of WebSocket connections
_user_connections: dict[str, set[WebSocket]] = defaultdict(set)
# facility_id -> set of (user_id, WebSocket) tuples
_facility_connections: dict[str, set[tuple[str, WebSocket]]] = defaultdict(set)
_lock = asyncio.Lock()


async def websocket_handler(websocket: WebSocket) -> None:
    """
    Starlette WebSocket endpoint for real-time task notifications.
    Auth via Firebase token in query param: /ws/tasks/?token=<firebase_id_token>
    After connection, client sends a JSON message with facility_id to subscribe.
    """
    await websocket.accept()

    user_id = None
    facility_id = None

    try:
        # Authenticate via query param token
        token = websocket.query_params.get("token")
        if not token:
            await websocket.send_json({"error": "Missing token parameter"})
            await websocket.close(code=4001)
            return

        user_id = await _verify_token(token)
        if not user_id:
            await websocket.send_json({"error": "Invalid token"})
            await websocket.close(code=4001)
            return

        await websocket.send_json({"type": "connected", "user_id": user_id})

        # Register user connection
        async with _lock:
            _user_connections[user_id].add(websocket)

        # Listen for messages
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "subscribe_facility":
                new_facility_id = data.get("facility_id")
                if new_facility_id:
                    async with _lock:
                        # Unsubscribe from old facility
                        if facility_id:
                            _facility_connections[facility_id].discard((user_id, websocket))
                        # Subscribe to new facility
                        facility_id = new_facility_id
                        _facility_connections[facility_id].add((user_id, websocket))
                    await websocket.send_json({
                        "type": "subscribed",
                        "facility_id": facility_id,
                    })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("WebSocket error: %s", e)
    finally:
        # Cleanup
        async with _lock:
            if user_id:
                _user_connections[user_id].discard(websocket)
                if not _user_connections[user_id]:
                    del _user_connections[user_id]
            if facility_id and user_id:
                _facility_connections[facility_id].discard((user_id, websocket))
                if not _facility_connections[facility_id]:
                    del _facility_connections[facility_id]


async def _verify_token(token: str) -> str | None:
    """Verify Firebase token and return app_user_id."""
    try:
        from app.auth.firebase_verifier import get_firebase_verifier
        from app.auth.user_sync import sync_firebase_user

        # Run sync Firebase operations in a thread
        loop = asyncio.get_event_loop()
        claims = await loop.run_in_executor(
            None, get_firebase_verifier().verify, token
        )
        app_user = await loop.run_in_executor(
            None, sync_firebase_user, claims
        )
        return str(app_user.id)
    except Exception as e:
        logger.warning("WebSocket auth failed: %s", e)
        return None


def broadcast_to_facility(facility_id: str, event: dict[str, Any]) -> None:
    """
    Send event to all WebSocket connections subscribed to a facility.
    Called from sync Django code — fires off async task.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_async_broadcast_facility(facility_id, event))
        else:
            loop.run_until_complete(_async_broadcast_facility(facility_id, event))
    except RuntimeError:
        # No event loop available (e.g., in a non-async context)
        # Create a new loop for this broadcast
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_async_broadcast_facility(facility_id, event))
            loop.close()
        except Exception:
            logger.debug("Could not broadcast to facility %s (no event loop)", facility_id)


def send_to_user(user_id: str, event: dict[str, Any]) -> None:
    """Send event to all WebSocket connections for a specific user."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_async_send_to_user(user_id, event))
        else:
            loop.run_until_complete(_async_send_to_user(user_id, event))
    except RuntimeError:
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_async_send_to_user(user_id, event))
            loop.close()
        except Exception:
            logger.debug("Could not send to user %s (no event loop)", user_id)


async def _async_broadcast_facility(facility_id: str, event: dict[str, Any]) -> None:
    async with _lock:
        connections = list(_facility_connections.get(facility_id, set()))

    dead = []
    for user_id, ws in connections:
        try:
            await ws.send_json(event)
        except Exception:
            dead.append((user_id, ws))

    if dead:
        async with _lock:
            for uid, ws in dead:
                _facility_connections[facility_id].discard((uid, ws))
                _user_connections.get(uid, set()).discard(ws)


async def _async_send_to_user(user_id: str, event: dict[str, Any]) -> None:
    async with _lock:
        connections = list(_user_connections.get(user_id, set()))

    dead = []
    for ws in connections:
        try:
            await ws.send_json(event)
        except Exception:
            dead.append(ws)

    if dead:
        async with _lock:
            for ws in dead:
                _user_connections[user_id].discard(ws)
