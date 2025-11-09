from app.schemas.user import UserCreate, User
from app.core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import Profile as ProfileModel
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.email == current_user['email']).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = ProfileModel(
        firebase_uid=current_user['user_id'],
        email=current_user['email'],
        full_name=user.full_name,
        phone_number=user.phone_number,
        profile_picture_url=user.profile_picture_url
    )


    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user