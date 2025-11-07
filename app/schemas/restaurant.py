#pydantic schemas for restaurant creation and display
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class RestaurantCreate(BaseModel):
    name: str
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    address: str
    latitude: str | None = None
    longitude: str | None = None
    phone_number: str | None = None
    email: str | None = None
    website_url: str | None = None
    operating_hours: str | None = None
    minimum_order_amount: int = 0
    average_delivery_time: int | None = None
    average_rating: int = 0
    total_reviews: int = 0
    owner_id: int

    model_config = ConfigDict(from_attributes=True)

class Restaurant(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    address: str
    latitude: str | None = None
    longitude: str | None = None
    phone_number: str | None = None
    email: str | None = None
    website_url: str | None = None
    operating_hours: str | None = None
    is_active: int
    minimum_order_amount: int
    average_delivery_time: int | None = None
    average_rating: int
    total_reviews: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RestaurantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    address: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    phone_number: str | None = None
    email: str | None = None
    website_url: str | None = None
    operating_hours: str | None = None
    is_active: int | None = None
    minimum_order_amount: int | None = None
    average_delivery_time: int | None = None
    average_rating: int | None = None
    total_reviews: int | None = None

    model_config = ConfigDict(from_attributes=True)

class MenuCategory(BaseModel):
    id: int
    restaurant_id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    