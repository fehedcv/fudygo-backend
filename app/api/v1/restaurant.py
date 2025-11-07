#endpoints of fastapi for restaurant operations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.restaurant import Restaurant as RestaurantModel
from app.schemas.restaurant import RestaurantCreate, Restaurant as RestaurantSchema
from app.core.auth import get_current_user

router = APIRouter()

#search for restaurants by name,minimum rating,location based on latitude and longitude,sort by(name,rating,distance),sort order asc or desc,page,size
@router.get("/", response_model=list[RestaurantSchema])
def search_restaurants(
    name: str | None = None,
    min_rating: int | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    sort_by: str | None = "name",
    sort_order: str | None = "asc",
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(RestaurantModel)

    if name:
        query = query.filter(RestaurantModel.name.ilike(f"%{name}%"))
    if min_rating:
        query = query.filter(RestaurantModel.average_rating >= min_rating)
    if latitude and longitude:
        # Simple bounding box for location filtering (not precise)
        lat_range = 0.1
        lon_range = 0.1
        query = query.filter(
            RestaurantModel.latitude.between(latitude - lat_range, latitude + lat_range),
            RestaurantModel.longitude.between(longitude - lon_range, longitude + lon_range)
        )

    if sort_by == "name":
        sort_column = RestaurantModel.name
    elif sort_by == "rating":
        sort_column = RestaurantModel.average_rating
    else:
        sort_column = RestaurantModel.name  # default

    if sort_order == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()

    query = query.order_by(sort_column)

    total = query.count()
    restaurants = query.offset((page - 1) * size).limit(size).all()

    return restaurants, total



