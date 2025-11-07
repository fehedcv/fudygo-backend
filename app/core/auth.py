# app/core/auth.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel



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

#check if user is admin by checking user_roles in the database
def is_admin_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == current_user["user_id"]).first()
    if not db_user or 'admin' not in db_user.roles:
        raise HTTPException(status_code=403, detail="Not authorized as admin")
    return True