from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, room_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)

            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: dict):
        disconnected_connections = []

        for connection in self.active_connections.get(room_id, []):
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_connections.append(connection)

        for connection in disconnected_connections:
            self.disconnect(room_id, connection)


manager = ConnectionManager()