"""
websocket/manager.py

Manages all active WebSocket connections from Vue dashboard clients.
The singleton `manager` instance is imported by events.py and the WS route.
"""

from fastapi import WebSocket
from typing import List
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Maintains a list of active WebSocket connections and broadcasts to all."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket client connected. Total: %d", len(self.active_connections)
        )

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            "WebSocket client disconnected. Total: %d", len(self.active_connections)
        )

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to every connected client.

        Dead connections are silently removed so they do not block the loop.
        """
        dead: List[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)

        for ws in dead:
            self.disconnect(ws)


# Singleton — import this everywhere
manager = ConnectionManager()
