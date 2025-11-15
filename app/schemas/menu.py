#pydantic schema for menu item
from pydantic import BaseModel, Field
from typing import Optional
from typing import List
from enum import Enum
from datetime import datetime

class MenuCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class MenuCategoryCreate(MenuCategoryBase):
    pass


class MenuCategoryResponse(MenuCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class MenuItemBase(BaseModel):
    restaurant_id: int
    category_id: int
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool = True


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_available: Optional[bool] = None
    category_id: Optional[int] = None


class MenuItemResponse(MenuItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
