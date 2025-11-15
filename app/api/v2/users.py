from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel
from app.schemas.user import UserCreate, User, UserUpdate
from app.core.auth import get_current_user, check_role, check_any_role

router = APIRouter()

# Shortcut for admin check
def AdminOnly():
    return check_role("admin")


# ────────────────────────────────────────────────────────────────
# ✔ Logged-in user → get own profile
# ────────────────────────────────────────────────────────────────

@router.get("/me", response_model=User)
def read_my_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_user = db.query(ProfileModel).filter(
        ProfileModel.firebase_uid == current_user["user_id"]
    ).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


# ────────────────────────────────────────────────────────────────
# ✔ Logged-in user → partially update own profile
# ────────────────────────────────────────────────────────────────

@router.patch("/me", response_model=User)
def update_my_user(
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_user = db.query(ProfileModel).filter(
        ProfileModel.firebase_uid == current_user["user_id"]
    ).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


# ────────────────────────────────────────────────────────────────
# ✔ Logged-in user → replace own profile
# ────────────────────────────────────────────────────────────────

@router.put("/me", response_model=User)
def replace_my_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_user = db.query(ProfileModel).filter(
        ProfileModel.firebase_uid == current_user["user_id"]
    ).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.full_name = user.full_name
    db_user.phone_number = user.phone_number
    db_user.profile_picture_url = user.profile_picture_url

    db.commit()
    db.refresh(db_user)
    return db_user


# ────────────────────────────────────────────────────────────────
# ✔ Logged-in user → update profile picture
# ────────────────────────────────────────────────────────────────

@router.patch("/me/profile-picture", response_model=User)
def update_profile_picture(
    profile_picture_url: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_user = db.query(ProfileModel).filter(
        ProfileModel.firebase_uid == current_user["user_id"]
    ).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.profile_picture_url = profile_picture_url

    db.commit()
    db.refresh(db_user)
    return db_user


# ────────────────────────────────────────────────────────────────
# ✔ Admin only → Search users by email
# ────────────────────────────────────────────────────────────────

@router.get("/search/", response_model=list[User], description="Search users by email (admin only)")
def search_users_by_email(
    email: str,
    db: Session = Depends(get_db),
    _ = Depends(AdminOnly())
):
    users = db.query(ProfileModel).filter(
        ProfileModel.email.ilike(f"%{email}%")
    ).all()
    return users


# ────────────────────────────────────────────────────────────────
# ✔ Admin only → Delete user by ID
# ────────────────────────────────────────────────────────────────

@router.delete("/{user_id}/", status_code=status.HTTP_204_NO_CONTENT, description="Delete user by ID (admin only)")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _ = Depends(AdminOnly())
):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return None


# ────────────────────────────────────────────────────────────────
# ✔ Admin only → Get user by ID
# ────────────────────────────────────────────────────────────────

@router.get("/{user_id}/", response_model=User, description="Get user by ID (admin only)")
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    _ = Depends(AdminOnly())
):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


# ────────────────────────────────────────────────────────────────
# ✔ Admin only → Get all users paginated
# ────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[User], description="Get all users (admin only)")
def get_all_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    _ = Depends(AdminOnly())
):
    users = db.query(ProfileModel).offset(skip).limit(limit).all()
    return users
