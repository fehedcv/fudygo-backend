from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CartItemBase(BaseModel):
    menu_item_id: int
    restaurant_id: int
    quantity: int
    price_per_item: float
    total_price: float
    notes: Optional[str] = None


class CartItemUpdate(BaseModel):
    notes: Optional[str] = None
    quantity: int



class CartItemResponse(CartItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    total_price: float
    total_items: int
    created_at: datetime
    updated_at: datetime
    items: List[CartItemResponse] = []

    class Config:
        orm_mode = True
