#endpoints of fastapi for user operations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel
from app.schemas.user import UserCreate, User

router = APIRouter()

@router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(ProfileModel).filter(ProfileModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = ProfileModel(
        email=user.email,
        password_hash=user.password,  # In real implementation, hash the password
        full_name=user.full_name,
        phone_number=user.phone_number,
        profile_picture_url=user.profile_picture_url,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
