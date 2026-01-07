from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.realtime.manager import manager
from app.core.ws_auth import authenticate_restaurant_ws, WSAuthError

router = APIRouter()


@router.websocket("/ws/orders/{restaurant_id}")
async def orders_ws(websocket: WebSocket, restaurant_id: int):
    try:
        auth_context = await authenticate_restaurant_ws(
            websocket=websocket,
            restaurant_id=restaurant_id,
        )
    except WSAuthError as e:
        await websocket.close(code=4403)
        return

    # ✅ Accept connection only AFTER auth and attach auth context
    await manager.connect(restaurant_id, websocket, auth_context)

    try:
        while True:
            await websocket.receive_text()  # keepalive
    except WebSocketDisconnect:
        manager.disconnect(restaurant_id, websocket)
