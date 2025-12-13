from typing import Dict, Set
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, restaurant_id: int, websocket: WebSocket):
        await websocket.accept()

        if restaurant_id not in self.active_connections:
            self.active_connections[restaurant_id] = set()

        self.active_connections[restaurant_id].add(websocket)
        print(f"✅ WS connected for restaurant {restaurant_id}")

    def disconnect(self, restaurant_id: int, websocket: WebSocket):
        if restaurant_id in self.active_connections:
            self.active_connections[restaurant_id].discard(websocket)

            if not self.active_connections[restaurant_id]:
                del self.active_connections[restaurant_id]

        print(f"❌ WS disconnected for restaurant {restaurant_id}")

    async def send_to_restaurant(self, restaurant_id: int, payload: dict):
        connections = self.active_connections.get(restaurant_id, set())

        for ws in connections:
            await ws.send_json(payload)


# 🔥 SINGLE SHARED INSTANCE
manager = ConnectionManager()
