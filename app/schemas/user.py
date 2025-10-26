#pydantic schemas for user creation and display
from pydantic import BaseModel, EmailStr
from datetime import datetime


'''
### User Profile Endpoints

#### GET `/users/me`
Get current user profile.

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):

{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "profile_picture_url": "url",
  "dietary_preferences": ["vegetarian"],
  "role": "customer",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}

'''

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: str
    profile_picture_url: str 
    role: str = "customer"
    created_at: datetime
    updated_at: datetime


class User