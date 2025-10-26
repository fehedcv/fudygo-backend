#endpoints of fastapi for user operations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel, Address as AddressOrmModel
from app.schemas.user import UserCreate, User, AddressModel, AddressCreate, UserUpdate

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


@router.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user  

#patch user
@router.patch("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return


#post profile picture url
@router.post("/users/{user_id}/profile-picture", response_model=User)
def update_profile_picture(user_id: int, profile_picture_url: str, db: Session =    Depends(get_db)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.profile_picture_url = profile_picture_url
    db.commit()
    db.refresh(db_user)
    return db_user


#get address list for user
@router.get("/users/{user_id}/addresses")
def get_user_addresses(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user.addresses

#add address for user
@router.post("/users/{user_id}/addresses", response_model=AddressModel)
def add_user_address(user_id: int, address: AddressCreate, db: Session = Depends(get_db)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    new_address = AddressOrmModel(**address.model_dump(), profile_id=user_id)
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address

#update address for user
@router.patch("/users/{user_id}/addresses/{address_id}", response_model=AddressModel)
def update_user_address(user_id: int, address_id: int, address: AddressCreate, db: Session = Depends(get_db)):
    db_address = db.query(AddressOrmModel).filter(AddressOrmModel.id == address_id, AddressOrmModel.profile_id == user_id).first()
    if db_address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    
    update_data = address.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_address, key, value)

    db.commit()
    db.refresh(db_address)
    return db_address
