#pydantic schema for menu item
from pydantic import BaseModel, Field
from typing import Optional
from typing import List
from enum import Enum

class MenuCategoryCreate(BaseModel):
    restaurant_id: int = Field(..., description="ID of the restaurant")
    name: str = Field(..., max_length=255, description="Name of the menu category")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the menu category")

class MenuCategory(BaseModel):
    id: int
    restaurant_id: int
    name: str
    description: Optional[str]

    class Config:
        orm_mode = True

class MenuItemCreate(BaseModel):
    category_id: int = Field(..., description="ID of the menu category")
    restaurant_id: int = Field(..., description="ID of the restaurant")
    name: str = Field(..., max_length=255, description="Name of the menu item")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the menu item")
    price: float = Field(..., gt=0, description="Price of the menu item")
    is_available: bool = Field(True, description="Availability status of the menu item")

class MenuItem(BaseModel):
    id: int
    category_id: int
    restaurant_id: int
    name: str
    description: Optional[str]
    price: float
    is_available: bool

    class Config:
        orm_mode = True     

class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Name of the menu item")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the menu item")
    price: Optional[float] = Field(None, gt=0, description="Price of the menu item")
    is_available: Optional[bool] = Field(None, description="Availability status of the menu item")
