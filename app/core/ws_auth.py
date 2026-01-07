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
    """Authenticate a WebSocket connection for restaurant POS access.

    Rules:
    - Must present `Authorization: Bearer <ID_TOKEN>` header (or `?token=` query fallback)
    - User must exist in Profile table
    - User must have role: admin OR manager (via custom claims or DB)
    - User must own the restaurant (Restaurant.owner_id)
    """

    # 1️⃣ Extract Authorization header or token query param
    auth_header = websocket.headers.get("authorization")
    token = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    else:
        # Fallback for clients that send token as query param
        token = websocket.query_params.get("token")

    if not token:
        raise WSAuthError("Missing Authorization Bearer token for websocket")

    # 2️⃣ Verify Firebase ID token
    try:
        decoded = auth.verify_id_token(token, check_revoked=True)
    except Exception:
        raise WSAuthError("Invalid or revoked Firebase ID token")

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

        # 4️⃣ Role check (admin OR manager) -- check DB roles
        if not user.roles or not any(role in user.roles for role in ["admin", "manager"]):
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