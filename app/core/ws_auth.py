from fastapi import WebSocket
from firebase_admin import auth
from sqlalchemy.orm import Session

from app.db.session import Session as SessionLocal
from app.models.user import Profile
from app.models.restaurant import Restaurant

class WSAuthError(Exception):
    pass


async def authenticate_restaurant_ws(
    websocket: WebSocket,
    restaurant_id: int,
):
    """
    Authenticate a WebSocket connection for restaurant POS access.

    Rules:
    - Must have valid Firebase session cookie
    - User must exist in Profile table
    - User must have role: admin OR manager
    - User must own the restaurant (Restaurant.owner_id)
    """

    # 1️⃣ Extract session cookie
    session_cookie = websocket.cookies.get("session")
    if not session_cookie:
        raise WSAuthError("Session cookie missing")

    # 2️⃣ Verify Firebase session
    try:
        decoded = auth.verify_session_cookie(
            session_cookie,
            check_revoked=True,
        )
    except Exception:
        raise WSAuthError("Invalid or expired session")

    firebase_uid = decoded.get("uid")
    if not firebase_uid:
        raise WSAuthError("Invalid Firebase payload")

    # 3️⃣ DB checks
    db: Session = SessionLocal()
    try:
        user = (
            db.query(Profile)
            .filter(Profile.firebase_uid == firebase_uid)
            .first()
        )

        if not user:
            raise WSAuthError("User not found")

        # 4️⃣ Role check (admin OR manager)
        if not user.roles or not any(
            role in user.roles for role in ["admin", "manager"]
        ):
            raise WSAuthError("Insufficient role")

        # 5️⃣ Restaurant ownership check
        restaurant = (
            db.query(Restaurant)
            .filter(Restaurant.id == restaurant_id)
            .first()
        )

        if not restaurant:
            raise WSAuthError("Restaurant not found")

        if restaurant.owner_id != user.id:
            raise WSAuthError("Not authorized for this restaurant")

        # ✅ AUTH SUCCESS
        return {
            "user": user,
            "restaurant": restaurant,
        }

    finally:
        db.close()