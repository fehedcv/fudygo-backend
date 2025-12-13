from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from firebase_admin import auth
from app.realtime.manager import manager

router = APIRouter()

@router.websocket("/ws/orders/{restaurant_id}")
async def orders_ws(websocket: WebSocket, restaurant_id: int):
    session_cookie = websocket.cookies.get("session")

    if not session_cookie:
        await websocket.close(code=4401)
        return

    try:
        auth.verify_session_cookie(session_cookie, check_revoked=True)
    except Exception:
        await websocket.close(code=4401)
        return

    await manager.connect(restaurant_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(restaurant_id, websocket)
