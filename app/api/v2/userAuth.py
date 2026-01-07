from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel
from app.schemas.user import User
from app.core.auth import get_current_user, check_any_role

router = APIRouter()


@router.get("/me", response_model=User)
def get_profile(current_user=Depends(get_current_user)):
    db_user = current_user["db_user"]
    return db_user


@router.get("/verify-manager")
def verify_manager(_=Depends(check_any_role(["manager", "admin"]))):
    return {"message": "User has manager or admin role"}