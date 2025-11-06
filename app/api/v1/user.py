#endpoints of fastapi for user operations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import Profile as ProfileModel, Address as AddressOrmModel, Role
from app.schemas.user import UserCreate, User, AddressModel, AddressCreate, UserUpdate
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.email == current_user['email']).first()
    if db_user:
        # If user exists, update firebase_uid if it's not set
        if not db_user.firebase_uid:
            db_user.firebase_uid = current_user['user_id']
            db.commit()
            db.refresh(db_user)
        return db_user

    # Fetch the customer role
    customer_role = db.query(Role).filter(Role.name == 'customer').first()
    if not customer_role:
        customer_role = Role(name='customer', description='A customer user')
        db.add(customer_role)
        db.commit()
        db.refresh(customer_role)

    new_user = ProfileModel(
        firebase_uid=current_user['user_id'],
        email=current_user['email'],
        full_name=user.full_name,
        phone_number=user.phone_number,
        profile_picture_url=user.profile_picture_url
    )
    
    new_user.roles.append(customer_role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login/", response_model=User)
def login(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.email == current_user['email']).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.email != current_user['email']:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    return db_user

#patch user
@router.patch("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.email != current_user['email']:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    
    update_data = user.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.email != current_user['email']:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    db.delete(db_user)
    db.commit()
    return


#post profile picture url
@router.post("/users/{user_id}/profile-picture", response_model=User)
def update_profile_picture(user_id: int, profile_picture_url: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.email != current_user['email']:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    
    db_user.profile_picture_url = profile_picture_url
    db.commit()
    db.refresh(db_user)
    return db_user


#get address list for user
@router.get("/users/{user_id}/addresses")
def get_user_addresses(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.email != current_user['email']:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    return db_user.addresses

#add address for user
@router.post("/users/{user_id}/addresses", response_model=AddressModel)
def add_user_address(user_id: int, address: AddressCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.email != current_user['email']:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    new_address = AddressOrmModel(**address.model_dump(), profile_id=user_id)
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address

#update address for user
@router.patch("/users/{user_id}/addresses/{address_id}", response_model=AddressModel)
def update_user_address(user_id: int, address_id: int, address: AddressCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = db.query(ProfileModel).filter(ProfileModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.email != current_user['email']:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    db_address = db.query(AddressOrmModel).filter(AddressOrmModel.id == address_id, AddressOrmModel.profile_id == user_id).first()
    if db_address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    
    update_data = address.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_address, key, value)

    db.commit()
    db.refresh(db_address)
    return db_address
