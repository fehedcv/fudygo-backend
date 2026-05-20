from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, asc, desc, text
import uuid
from app.schemas.restaurant import RestaurantCreate, Restaurant as RestaurantSchema, RestaurantUpdate, SearchResult as SearchResultSchema
from typing import List, Optional
from app.db.session import get_db
from app.models.restaurant import Restaurant as RestaurantModel, MenuItem as MenuItemModel
from app.models.user import Profile as ProfileModel
from app.core.auth import get_current_user, check_role, add_role, check_any_role
from app.models.user import Profile
from app.models.restaurant import MenuCategory 
from app.schemas.menu import MenuCategoryResponse, MenuCategoryCreate

router = APIRouter()

@router.get("/", response_model=List[RestaurantSchema], status_code=status.HTTP_200_OK)
def search_restaurants(
    name: Optional[str] = Query(None, description="Search restaurants by name"),
    min_rating: Optional[float] = Query(None, description="Minimum average rating"),
    latitude: Optional[float] = Query(None, description="User latitude for location search"),
    longitude: Optional[float] = Query(None, description="User longitude for location search"),
    sort_by: Optional[str] = Query("name", enum=["name", "rating", "distance"]),
    sort_order: Optional[str] = Query("asc", enum=["asc", "desc"]),
    pickup: Optional[bool] = Query(None, description="Filter for pickup-only restaurants"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(RestaurantModel)

    if name:
        query = query.filter(RestaurantModel.name.ilike(f"%{name}%"))

    if min_rating is not None:
        query = query.filter(RestaurantModel.average_rating >= min_rating)

    distance_column = None
    if latitude is not None and longitude is not None:
        # Only consider restaurants that have coordinates
        query = query.filter(
            RestaurantModel.latitude.isnot(None),
            RestaurantModel.longitude.isnot(None),
        )

        # Haversine distance in km
        distance_column = (
            6371
            * func.acos(
                func.least(
                    1.0,
                    func.cos(func.radians(latitude))
                    * func.cos(func.radians(RestaurantModel.latitude))
                    * func.cos(func.radians(RestaurantModel.longitude) - func.radians(longitude))
                    + func.sin(func.radians(latitude))
                    * func.sin(func.radians(RestaurantModel.latitude)),
                )
            )
        ).label("distance_km")

        query = query.add_columns(distance_column)

        # ✅ THE MISSING PIECE: only return restaurants whose delivery radius covers the user
        query = query.filter(distance_column <= RestaurantModel.delivery_radius_km)

    # Sorting
    if sort_by == "distance" and distance_column is not None:
        order_col = distance_column
    elif sort_by == "rating":
        order_col = RestaurantModel.average_rating
    else:
        order_col = RestaurantModel.name

    query = query.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

    # Pagination — count before applying offset/limit
    # Use subquery to avoid count() issues with add_columns
    if distance_column is not None:
        total = query.with_entities(RestaurantModel.id).count()
    else:
        total = query.count()

    restaurants = query.offset((page - 1) * size).limit(size).all()

    # Unwrap tuples when distance column was added
    if distance_column is not None:
        restaurants = [r[0] for r in restaurants]

    return restaurants 


#get restaurants based on eligibility to user
@router.get("/delivering-to")
def restaurants_delivering_to(
    lat: float = Query(...),
    lng: float = Query(...),
    db: Session = Depends(get_db)
):
    point = {
        "lat": lat,
        "lng": lng
    }

    query = text("""
        SELECT
            id,
            name,
            slug,
            address,
            logo_url,
            delivery_radius_km,
            latitude,
            longitude,
            ST_Distance(
                location,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
            ) AS distance
        FROM restaurants
        WHERE ST_DWithin(
            location,
            ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
            delivery_radius_km * 1000
        )
        ORDER BY distance ASC;
    """)

    rows = db.execute(query, point).fetchall()

    results = []
    for r in rows:
        results.append({
            "id": r.id,
            "name": r.name,
            "slug": r.slug,
            "address": r.address,
            "logo_url": r.logo_url,
            "distance_km": round(r.distance / 1000, 2),
            "delivery_radius_km": r.delivery_radius_km,
            "latitude": r.latitude,
            "longitude": r.longitude
        })

    return results


@router.get("/search", response_model=List[SearchResultSchema])
def search_food_and_restaurants(
    query: str = Query(..., min_length=1, description="Search by food item or restaurant name"),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    """Search restaurants by name or food items, filtered to those delivering to the user's location."""

    # Base filters applied to every restaurant query
    base_filters = [RestaurantModel.is_active == 1]

    # When coordinates are provided, restrict to restaurants whose delivery radius covers the user
    # Uses the same PostGIS ST_DWithin logic as /delivering-to
    if latitude is not None and longitude is not None:
        deliverable_ids_query = text("""
            SELECT id FROM restaurants
            WHERE ST_DWithin(
                location,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                delivery_radius_km * 1000
            )
        """)
        rows = db.execute(deliverable_ids_query, {"lat": latitude, "lng": longitude}).fetchall()
        deliverable_ids = [row[0] for row in rows]
        base_filters.append(RestaurantModel.id.in_(deliverable_ids))

    # Restaurants whose name matches
    name_matched = (
        db.query(RestaurantModel)
        .filter(*base_filters, RestaurantModel.name.ilike(f"%{query}%"))
        .all()
    )

    # Restaurants that have at least one menu item matching
    food_restaurant_ids = (
        db.query(MenuItemModel.restaurant_id)
        .filter(MenuItemModel.name.ilike(f"%{query}%"), MenuItemModel.is_available == True)
        .distinct()
        .subquery()
    )
    food_matched = (
        db.query(RestaurantModel)
        .filter(*base_filters, RestaurantModel.id.in_(food_restaurant_ids))
        .all()
    )

    results = []
    seen_ids = set()

    # Food matches first (higher relevance)
    for restaurant in food_matched:
        matching_items = (
            db.query(MenuItemModel)
            .filter(
                MenuItemModel.restaurant_id == restaurant.id,
                MenuItemModel.name.ilike(f"%{query}%"),
                MenuItemModel.is_available == True,
            )
            .limit(6)
            .all()
        )
        results.append({"restaurant": restaurant, "menu_items": matching_items, "match_type": "food"})
        seen_ids.add(restaurant.id)

    # Restaurant name matches (show up to 6 available items)
    for restaurant in name_matched:
        if restaurant.id not in seen_ids:
            items = (
                db.query(MenuItemModel)
                .filter(MenuItemModel.restaurant_id == restaurant.id, MenuItemModel.is_available == True)
                .limit(6)
                .all()
            )
            results.append({"restaurant": restaurant, "menu_items": items, "match_type": "restaurant"})
            seen_ids.add(restaurant.id)

    return results


@router.get("/{restaurant_id}", response_model=RestaurantSchema)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant

@router.post(
    "/",
    response_model=RestaurantSchema,
    status_code=status.HTTP_201_CREATED,
    description="Create a restaurant for another user (admin only)"
)
def create_restaurant_for_user(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    _ = Depends(check_role("admin"))
):
    # -------------------------
    # 1. Validate owner existence
    # -------------------------
    owner = db.query(ProfileModel).filter(ProfileModel.id == restaurant.owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=404,
            detail=f"Owner with id {restaurant.owner_id} does not exist"
        )

    # -------------------------
    # 2. Generate unique slug
    # -------------------------
    try:
        slug = restaurant.name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating slug: {str(e)}"
        )

    # -------------------------
    # 3. Create Restaurant Object
    # -------------------------
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
        owner_id=restaurant.owner_id,
        delivery_radius_km=restaurant.delivery_radius_km,   # ✅ NEW
    )

    # -------------------------
    # 4. Sync PostGIS location (longitude then latitude)
    # -------------------------
    try:
        if restaurant.latitude and restaurant.longitude:
            db_restaurant.location = f"POINT({restaurant.longitude} {restaurant.latitude})"
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid coordinates: {str(e)}"
        )

    # -------------------------
    # 5. Add manager role safely
    # -------------------------
    try:
        add_role(db, restaurant.owner_id, "manager")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding manager role: {str(e)}"
        )

    # -------------------------
    # 6. Save Restaurant with full DB error handling
    # -------------------------
    try:
        db.add(db_restaurant)
        db.commit()
        db.refresh(db_restaurant)
        return db_restaurant

    except IntegrityError as e:
        db.rollback()

        # Unique constraint errors
        if 'slug' in str(e.orig):
            raise HTTPException(
                status_code=400,
                detail="A restaurant with a similar slug already exists. Try again."
            )
        if 'owner_id' in str(e.orig):
            raise HTTPException(
                status_code=400,
                detail="Invalid owner_id or owner already holds a conflicting record."
            )

        raise HTTPException(
            status_code=400,
            detail=f"Database integrity error: {str(e.orig)}"
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )
    

@router.put("/{restaurant_id}/", response_model=RestaurantSchema, description="Update restaurant info (admin only)")
def update_restaurant_info(
    restaurant_id: int,
    restaurant_update: RestaurantCreate,
    db: Session = Depends(get_db),
    _ = Depends(check_role("admin"))
):
    db_restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    for key, value in restaurant_update.dict().items():
        setattr(db_restaurant, key, value)
    
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


@router.patch("/{restaurant_id}/", response_model=RestaurantSchema, description="Patch restaurant info (admin only)")
def patch_restaurant_info(
    restaurant_id: int,
    restaurant_update: RestaurantUpdate,
    db: Session = Depends(get_db),
    _ = Depends(check_role("admin"))
):
    db_restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    for key, value in restaurant_update.dict(exclude_unset=True).items():
        setattr(db_restaurant, key, value)
    
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


@router.delete("/{restaurant_id}/", status_code=status.HTTP_204_NO_CONTENT, description="Delete restaurant (admin only)")
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    _ = Depends(check_role("admin"))
):
    db_restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    db.delete(db_restaurant)
    db.commit()
    return None


@router.get("/{restaurant_id}/categories", response_model=list[MenuCategoryResponse])
def get_categories_for_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    categories = (
        db.query(MenuCategory)
        .filter(MenuCategory.restaurant_id == restaurant_id)
        .all()
    )
    return categories


@router.post(
    "/{restaurant_id}/categories",
    response_model=MenuCategoryResponse,
    status_code=201
)
def create_category_for_restaurant(
    restaurant_id: int,
    payload: MenuCategoryCreate,
    db: Session = Depends(get_db),
    _ = Depends(check_any_role(["manager", "admin"]))
):

    new_category = MenuCategory(
        restaurant_id=restaurant_id,   # ← FIXED
        **payload.dict()               # name + description only
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

#get my restaurants for manager
@router.get("/my-restaurants/", response_model=List[RestaurantSchema],
            description="Get restaurants for the logged-in manager")
def get_my_restaurants(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _ = Depends(check_role("manager"))
):
    profile = db.query(Profile).filter(Profile.firebase_uid == current_user["user_id"]).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    restaurants = (
        db.query(RestaurantModel)
        .filter(RestaurantModel.owner_id == profile.id)
        .all()
    )

    return restaurants