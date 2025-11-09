# app/core/auth.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel
from sqlalchemy import update, func
from app.models.user import Profile as User



security = HTTPBearer()

def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token  # includes user_id, email, etc.
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_current_user(decoded_token: dict = Depends(verify_firebase_token)):
    user_id = decoded_token.get("uid")
    email = decoded_token.get("email")
    if not user_id or not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"user_id": user_id, "email": email}


def check_role(
    role: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.roles or role not in db_user.roles:
        raise HTTPException(status_code=403, detail=f"Not authorized as {role}")

    return True


#function to check if any of the role is in user
def check_any_role(
    roles: list[str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.roles or not any(role in db_user.roles for role in roles):
        raise HTTPException(status_code=403, detail=f"Not authorized with required roles")

    return True

def add_role(db, user_id: int, role: str):
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(roles=func.array_append(func.coalesce(User.roles, '{}'), role))
    )
    db.execute(stmt)
    db.commit()