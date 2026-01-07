from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    """Manage active websocket connections per restaurant.

    Each restaurant maps to a dict of `WebSocket` -> `auth_context` (dict).
    Storing the auth context lets the app later inspect the authenticated user
    associated with a connection (e.g., for permissions, auditing).
    """

    def __init__(self):
        self.active_connections: Dict[int, Dict[WebSocket, dict]] = {}

    async def connect(self, restaurant_id: int, websocket: WebSocket, auth_context: dict | None = None):
        await websocket.accept()

        if restaurant_id not in self.active_connections:
            self.active_connections[restaurant_id] = {}

        # store websocket -> auth context mapping
        self.active_connections[restaurant_id][websocket] = auth_context or {}
        print(f"✅ WS connected for restaurant {restaurant_id}")

    def disconnect(self, restaurant_id: int, websocket: WebSocket):
        if restaurant_id in self.active_connections:
            self.active_connections[restaurant_id].pop(websocket, None)

            if not self.active_connections[restaurant_id]:
                del self.active_connections[restaurant_id]

        print(f"❌ WS disconnected for restaurant {restaurant_id}")

    async def send_to_restaurant(self, restaurant_id: int, payload: dict):
        connections = self.active_connections.get(restaurant_id, {})

        for ws in list(connections.keys()):
            await ws.send_json(payload)

    def get_auth_for_websocket(self, restaurant_id: int, websocket: WebSocket) -> dict | None:
        return self.active_connections.get(restaurant_id, {}).get(websocket)


# 🔥 SINGLE SHARED INSTANCE
manager = ConnectionManager()
