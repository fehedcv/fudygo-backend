from pydantic import BaseModel, ConfigDict
from typing import List, Optional


# ─────────────────────────────────────────────
# Cart Item Schemas
# ─────────────────────────────────────────────

class CartItemBase(BaseModel):
    menu_item_id: int
    restaurant_id: int
    quantity: int = 1
    notes: Optional[str] = None


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    menu_item_id: int
    restaurant_id: int
    quantity: int
    price_per_item: float
    total_price: float
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# Cart Schemas
# ─────────────────────────────────────────────

class CartResponse(BaseModel):
    id: int
    total_amount: float
    total_items: int
    items: List[CartItemResponse]

    model_config = ConfigDict(from_attributes=True)
