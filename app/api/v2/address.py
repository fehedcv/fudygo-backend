from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel, Address as AddressOrmModel
from app.schemas.user import  AddressModel,AddressUpdate, AddressCreate
from app.core.auth import get_current_user

router = APIRouter()

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


@router.patch("/addresses/me/{address_id}", response_model=AddressModel)
def update_my_address(
    address_id: int,
    address: AddressUpdate,
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


#put address for user
@router.put("/addresses/me/{address_id}", response_model=AddressModel)
def replace_my_address(
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

    # Replace all fields of the address
    for key, value in address.model_dump().items():
        setattr(db_address, key, value)

    db.commit()
    db.refresh(db_address)
    return db_address


#delete address for user
@router.delete("/addresses/me/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_address(
    address_id: int,
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

    db.delete(db_address)
    db.commit()
    return None

#set default address for user patch
'''@router.patch("/addresses/me/{address_id}/default", response_model=AddressModel)
def set_default_my_address(
    address_id: int,
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

    # Set all other addresses to not default
    db.query(AddressOrmModel).filter(
        AddressOrmModel.profile_id == db_user.id,
        AddressOrmModel.id != address_id
    ).update({AddressOrmModel.is_default: False})

    # Set this address as default
    db_address.is_default = True

    db.commit()
    db.refresh(db_address)
    return db_address'''


