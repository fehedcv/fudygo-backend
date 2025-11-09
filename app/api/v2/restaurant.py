from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc
import uuid
from app.schemas.restaurant import RestaurantCreate, Restaurant as RestaurantSchema 
from typing import List, Optional
from app.db.session import get_db
from app.models.restaurant import Restaurant as RestaurantModel
from app.core.auth import get_current_user, check_role, add_role, check_any_role
from app.schemas.menu import MenuCategory, MenuCategoryCreate
from app.models.user import Profile
from app.models.restaurant import MenuCategory as MenuCategoryModel

router = APIRouter()

@router.get("/", response_model=List[RestaurantSchema], status_code=status.HTTP_200_OK)
def search_restaurants(
    name: Optional[str] = Query(None, description="Search restaurants by name"),
    min_rating: Optional[float] = Query(None, description="Minimum average rating"),
    latitude: Optional[float] = Query(None, description="User latitude for location search"),
    longitude: Optional[float] = Query(None, description="User longitude for location search"),
    sort_by: Optional[str] = Query("name", enum=["name", "rating", "distance"]),
    sort_order: Optional[str] = Query("asc", enum=["asc", "desc"]),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    """
    🔎 Search restaurants by name, rating, and location.
    Supports sorting by name, rating, or distance, with pagination.
    """

    query = db.query(RestaurantModel)

    # 🧭 Filter by name
    if name:
        query = query.filter(RestaurantModel.name.ilike(f"%{name}%"))

    # ⭐ Filter by minimum rating
    if min_rating is not None:
        query = query.filter(RestaurantModel.average_rating >= min_rating)

    # 📍 Optional: distance calculation if lat/lon provided
    distance_column = None
    if latitude is not None and longitude is not None:
        # Haversine formula (distance in km)
        distance_column = (
            6371
            * func.acos(
                func.least(
                    1.0,
                    func.cos(func.radians(latitude))
                    * func.cos(func.radians(RestaurantModel.latitude))
                    * func.cos(func.radians(RestaurantModel.longitude) - func.radians(longitude))
                    + func.sin(func.radians(latitude))
                    * func.sin(func.radians(RestaurantModel.latitude))
                )
            )
        ).label("distance_km")

        query = query.add_columns(distance_column)

    # 🧮 Sorting
    if sort_by == "name":
        order_col = RestaurantModel.name
    elif sort_by == "rating":
        order_col = RestaurantModel.average_rating
    elif sort_by == "distance" and distance_column is not None:
        order_col = distance_column
    else:
        order_col = RestaurantModel.name

    query = query.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

    # 📊 Pagination
    total = query.count()
    restaurants = query.offset((page - 1) * size).limit(size).all()

    # 💡 If you added distance_column, results are tuples: (Restaurant, distance)
    if distance_column is not None:
        restaurants = [r[0] for r in restaurants]

    return restaurants


@router.get("/{restaurant_id}", response_model=RestaurantSchema)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant


@router.post("/restaurants/", response_model=RestaurantSchema, status_code=status.HTTP_201_CREATED, description="Create a restaurant for another user (admin only)")
def create_restaurant_for_user(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_role("admin", current_user, db):
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

    #add manager role to the user if not already
    add_role(db, restaurant.owner_id, "manager")
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


@router.put("/restaurants/{restaurant_id}/", response_model=RestaurantSchema, description="Update restaurant info (admin only)")
def update_restaurant_info(
    restaurant_id: int,
    restaurant_update: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_role("admin", current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized to update restaurant info")
    
    db_restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    for key, value in restaurant_update.dict().items():
        setattr(db_restaurant, key, value)
    
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


@router.patch("/restaurants/{restaurant_id}/", response_model=RestaurantSchema, description="Patch restaurant info (admin only)")
def patch_restaurant_info(
    restaurant_id: int,
    restaurant_update: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_role("admin", current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized to update restaurant info")
    
    db_restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    for key, value in restaurant_update.dict(exclude_unset=True).items():
        setattr(db_restaurant, key, value)
    
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


@router.delete("/restaurants/{restaurant_id}/", status_code=status.HTTP_204_NO_CONTENT, description="Delete restaurant (admin only)")
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_role("admin", current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete restaurant")
    
    db_restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    db.delete(db_restaurant)
    db.commit()
    return "deleted successfully"


@router.get("/{restaurant_id}/categories", response_model=List[MenuCategory])
def get_restaurant_categories(restaurant_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    categories = db.query(MenuCategory).filter(MenuCategory.restaurant_id == restaurant_id).all()
    return categories


#create menu category for restaurant (admin or manager only)
@router.post("/categories", response_model=MenuCategory, status_code=status.HTTP_201_CREATED)
def create_menu_category_for_restaurant(
    category: MenuCategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_any_role(["admin", "manager"], current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized to create menu category")
    
    db_category = MenuCategoryModel(
        name=category.name,
        description=category.description,
        restaurant_id=category.restaurant_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


#get my restaurants for manager
@router.get("/my-restaurants/", response_model=List[RestaurantSchema],
            description="Get restaurants for the logged-in manager")
def get_my_restaurants(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_role("manager", current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized as manager")
    
    profile = db.query(Profile).filter(Profile.firebase_uid == current_user["user_id"]).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    restaurants = (
        db.query(RestaurantModel)
        .filter(RestaurantModel.owner_id == profile.id)
        .all()
    )

    return restaurants
