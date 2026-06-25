from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.connection_manager import manager
from app.core.security import validate_token

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # Authenticate the connection by validating the JWT access token.
    try:
        payload = validate_token(token, "access")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token payload is missing the user identifier.")
    except Exception:
        await websocket.close(code=1008)
        return

    user_id = str(user_id)
    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "subscribe":
                tank_id = data.get("tank_id")
                if tank_id:
                    await manager.subscribe_to_tank(websocket, tank_id)
                    await websocket.send_json({"status": "subscribed", "tank_id": tank_id})

            elif data.get("action") == "unsubscribe":
                tank_id = data.get("tank_id")
                if tank_id:
                    await manager.unsubscribe_from_tank(websocket, tank_id)
                    await websocket.send_json({"status": "unsubscribed", "tank_id": tank_id})

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
