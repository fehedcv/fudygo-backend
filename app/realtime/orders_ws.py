from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from firebase_admin import auth
from app.realtime.manager import manager
from app.db.session import Session as SessionLocal
from app.models.user import Profile
from app.models.restaurant import Restaurant

router = APIRouter()


@router.websocket("/ws/orders/{restaurant_id}")
async def orders_ws(websocket: WebSocket, restaurant_id: int, token: str = Query(None)):
    await websocket.accept()

    if not token:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    try:
        decoded = auth.verify_id_token(token, check_revoked=True)
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    firebase_uid = decoded.get("uid")
    if not firebase_uid:
        await websocket.close(code=4001, reason="Invalid token")
        return

    db = SessionLocal()
    try:
        user = db.query(Profile).filter(Profile.firebase_uid == firebase_uid).first()
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return

        if not user.roles or not any(role in user.roles for role in ["admin", "manager"]):
            await websocket.close(code=4001, reason="Insufficient role")
            return

        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            await websocket.close(code=4001, reason="Restaurant not found")
            return

        if restaurant.owner_id != user.id:
            await websocket.close(code=4001, reason="Not authorized for this restaurant")
            return

        auth_context = {"user": user, "restaurant": restaurant}
    finally:
        db.close()

    # Register directly — websocket is already accepted above
    if restaurant_id not in manager.active_connections:
        manager.active_connections[restaurant_id] = {}
    manager.active_connections[restaurant_id][websocket] = auth_context

    try:
        while True:
            await websocket.receive_text()  # keepalive
    except WebSocketDisconnect:
        manager.disconnect(restaurant_id, websocket)
