from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.restaurant import Restaurant as RestaurantModel
from app.models.user import Profile as UserModel
from app.schemas.user import User as UserSchema
from app.schemas.restaurant import RestaurantCreate, Restaurant as RestaurantSchema
from app.core.auth import get_current_user, is_admin_user
import uuid

router = APIRouter()

#to create a restaurant for another user (admin only)
@router.post("/restaurants/", response_model=RestaurantSchema, status_code=status.HTTP_201_CREATED)
def create_restaurant_for_user(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not is_admin_user(current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized to create restaurant for another user")
    
    # Generate a unique slug for the restaurant
    slug = restaurant.name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    
    db_restaurant = RestaurantModel(
        slug=slug,
        name=restaurant.name,
        description=restaurant.description,
        logo_url=restaurant.logo_url,
        banner_url=restaurant.banner_url,
        address=restaurant.address,
        latitude=restaurant.latitude,
        longitude=restaurant.longitude,
        phone_number=restaurant.phone_number,
        email=restaurant.email,
        website_url=restaurant.website_url,
        operating_hours=restaurant.operating_hours,
        minimum_order_amount=restaurant.minimum_order_amount,
        average_delivery_time=restaurant.average_delivery_time,
        owner_id=restaurant.owner_id
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

#search users by email (admin only)
@router.get("/users/search/", response_model=list[UserSchema])
def search_users_by_email(
    email: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not is_admin_user(current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized to search users")
    
    users = db.query(UserModel).filter(UserModel.email.ilike(f"%{email}%")).all()
    return users
