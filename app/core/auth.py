# app/core/auth.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel
from sqlalchemy import update, func
from app.models.user import Profile as User
import datetime


security = HTTPBearer()



# 🔹 Verify Firebase session cookie
def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Session cookie missing")

    try:
        decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
    except auth.InvalidSessionCookieError:
        raise HTTPException(status_code=401, detail="Invalid or expired session cookie")

    # Check if user exists in DB
    firebase_uid = decoded_claims.get("uid")
    email = decoded_claims.get("email")
    if not firebase_uid or not email:
        raise HTTPException(status_code=401, detail="Invalid Firebase payload")

    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == firebase_uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user_id": firebase_uid, "email": email, "db_user": db_user}

# 🔹 Create a Firebase session cookie
def create_session_cookie(id_token: str):
    try:
        expires_in = datetime.timedelta(days=14)  # max 2 weeks
        session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in)
        return session_cookie
    except Exception:
        raise HTTPException(status_code=401, detail="Failed to create session cookie")

# 🔹 Logout + revoke tokens
def logout_user(firebase_uid: str):
    try:
        auth.revoke_refresh_tokens(firebase_uid)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to revoke Firebase tokens")
    

'''def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
    return {"user_id": user_id, "email": email}'''


def check_role(role: str):
    def role_checker(
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
    return role_checker


#function to check if any of the role is in user
def check_any_role(roles: list[str]):
    def role_checker(
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
    return role_checker

def add_role(db, user_id: int, role: str):
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(roles=func.array_append(func.coalesce(User.roles, '{}'), role))
    )
    db.execute(stmt)
    db.commit()