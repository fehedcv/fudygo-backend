#endpoints of fastapi for user operations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel, Address as AddressOrmModel
from app.schemas.user import UserCreate, User, AddressModel, AddressCreate, UserUpdate
from app.core.auth import get_current_user

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


'''@router.post("/login/", response_model=User)
def login(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.email == current_user['email']).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user'''


@router.get("/me", response_model=User)
def read_my_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Find the logged-in user's profile using their email from the token
    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == current_user["user_id"]).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user

#patch user
@router.patch("/me", response_model=User)
def update_my_user(
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Get the logged-in user's profile
    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == current_user["user_id"]).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Update only the fields that were provided
    update_data = user.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user



'''@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.email != current_user['email']:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    db.delete(db_user)
    db.commit()
    return'''


#to update profile picture url
@router.patch("/me/profile-picture", response_model=User)
def update_profile_picture(
    profile_picture_url: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Get the logged-in user's profile
    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == current_user["user_id"]).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Update the profile picture URL
    db_user.profile_picture_url = profile_picture_url
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/addresses/me", response_model=list[AddressModel])
def get_my_addresses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Get the logged-in user's profile
    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == current_user["user_id"]).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Return all addresses linked to this profile
    return db_user.addresses


@router.post("/addresses/me", response_model=AddressModel)
def add_my_address(
    address: AddressCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Get the logged-in user's profile
    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == current_user["user_id"]).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Create a new address linked to the user
    new_address = AddressOrmModel(**address.model_dump(), profile_id=db_user.id)

    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return new_address

#update address for user
@router.patch("/addresses/me/{address_id}", response_model=AddressModel)
def update_my_address(
    address_id: int,
    address: AddressCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Get the current user's profile
    db_user = db.query(ProfileModel).filter(ProfileModel.firebase_uid == current_user["user_id"]).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Get the address belonging to this user
    db_address = (
        db.query(AddressOrmModel)
        .filter(AddressOrmModel.id == address_id, AddressOrmModel.profile_id == db_user.id)
        .first()
    )
    if db_address is None:
        raise HTTPException(status_code=404, detail="Address not found")

    # Update only the provided fields
    update_data = address.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_address, key, value)

    db.commit()
    db.refresh(db_address)
    return db_address

