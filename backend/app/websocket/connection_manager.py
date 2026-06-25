from typing import Dict, List, Any
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Maps user_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Maps tank_id -> List[WebSocket]
        self.tank_subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
        # Remove from subscriptions
        for tank_id in list(self.tank_subscriptions.keys()):
            if websocket in self.tank_subscriptions[tank_id]:
                self.tank_subscriptions[tank_id].remove(websocket)

    async def subscribe_to_tank(self, websocket: WebSocket, tank_id: str):
        if tank_id not in self.tank_subscriptions:
            self.tank_subscriptions[tank_id] = []
        if websocket not in self.tank_subscriptions[tank_id]:
            self.tank_subscriptions[tank_id].append(websocket)

    async def unsubscribe_from_tank(self, websocket: WebSocket, tank_id: str):
        if tank_id in self.tank_subscriptions and websocket in self.tank_subscriptions[tank_id]:
            self.tank_subscriptions[tank_id].remove(websocket)

    async def broadcast_to_tank(self, tank_id: str, message: Any):
        if tank_id in self.tank_subscriptions:
            dead_connections = []
            for connection in self.tank_subscriptions[tank_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)
            
            # Cleanup dead connections
            for conn in dead_connections:
                for uid in list(self.active_connections.keys()):
                    if conn in self.active_connections[uid]:
                        self.disconnect(conn, uid)

manager = ConnectionManager()
