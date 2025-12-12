# pydantic schemas for restaurant creation and display
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


# ---------------------------------------------------------
# CREATE RESTAURANT SCHEMA
# ---------------------------------------------------------
class RestaurantCreate(BaseModel):
    name: str
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    address: str

    # Coordinates must be float for PostGIS
    latitude: float | None = Field(default=None, description="Latitude in decimal degrees")
    longitude: float | None = Field(default=None, description="Longitude in decimal degrees")

    phone_number: str | None = None
    email: str | None = None
    website_url: str | None = None
    operating_hours: str | None = None

    minimum_order_amount: int = 0
    average_delivery_time: int | None = None
    average_rating: int = 0
    total_reviews: int = 0

    # Delivery radius for restaurant-specific delivery
    delivery_radius_km: float = Field(default=5, description="Delivery radius in kilometers")

    owner_id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# RESPONSE SCHEMA FOR RESTAURANT
# ---------------------------------------------------------
class Restaurant(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    address: str

    # FIXED: floats instead of strings
    latitude: float | None = None
    longitude: float | None = None

    phone_number: str | None = None
    email: str | None = None
    website_url: str | None = None
    operating_hours: str | None = None

    is_active: int
    minimum_order_amount: int
    average_delivery_time: int | None = None
    average_rating: int
    total_reviews: int

    # Must be included in API response
    delivery_radius_km: float

    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# UPDATE SCHEMA FOR PARTIAL UPDATES
# ---------------------------------------------------------
class RestaurantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    address: str | None = None

    # FIXED: floats instead of strings
    latitude: float | None = None
    longitude: float | None = None

    phone_number: str | None = None
    email: str | None = None
    website_url: str | None = None
    operating_hours: str | None = None

    is_active: int | None = None
    minimum_order_amount: int | None = None
    average_delivery_time: int | None = None
    average_rating: int | None = None
    total_reviews: int | None = None

    # Added for update support
    delivery_radius_km: float | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# MENUS / CATEGORY (unchanged)
# ---------------------------------------------------------
class MenuCategory(BaseModel):
    id: int
    restaurant_id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
