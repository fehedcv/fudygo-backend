#pydantic schemas for user creation and display
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime




class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: str
    profile_picture_url: str 
    role: str = "customer"
    created_at: datetime
    updated_at: datetime


class User(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone_number: str | None = None
    profile_picture_url: str | None = None
    role: str
    is_active: int
    is_verified: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    phone_number: str | None = None
    profile_picture_url: str | None = None
    role: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AddressCreate(BaseModel):
    label: str
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    post_code: str
    is_default: int = 0

    model_config = ConfigDict(from_attributes=True)


class AddressModel(BaseModel):
    id: int
    profile_id: int
    label: str
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    post_code: str
    latitude: str | None = None
    longitude: str | None = None
    is_default: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
