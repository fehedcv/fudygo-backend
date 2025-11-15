from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# -----------------------------
# Order Item Schema
# -----------------------------
class OrderItem(BaseModel):
    item_id: int
    name: Optional[str] = None
    quantity: int
    price: int
    total: int


# -----------------------------
# Status History Schema
# -----------------------------
class OrderStatusHistorySchema(BaseModel):
    id: int
    status: str
    updated_by: str
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }


# -----------------------------
# Base Order Schema
# -----------------------------
class OrderBase(BaseModel):
    restaurant_id: int
    delivery_address_id: Optional[int] = None
    order_type: str
    items: List[Any]
    subtotal_amount: int
    discount_amount: Optional[int] = 0
    delivery_fee: Optional[int] = 0
    tax_amount: Optional[int] = 0
    total_amount: int
    payment_method: str
    special_instructions: Optional[str] = None
    scheduled_time: Optional[datetime] = None


# -----------------------------
# Create Order Schema (POST)
# -----------------------------
class OrderCreate(OrderBase):
    pass


# -----------------------------
# Response Schema
# -----------------------------
class OrderResponse(BaseModel):
    id: int
    order_number: str

    user_id: int
    restaurant_id: int
    delivery_address_id: Optional[int]

    order_type: str
    status: str
    scheduled_time: Optional[datetime]

    items: List[Any]  # expanded list of items

    subtotal_amount: int
    discount_amount: int
    delivery_fee: int
    tax_amount: int
    total_amount: int

    payment_method: str
    payment_status: str
    special_instructions: Optional[str]
    estimated_delivery_time: Optional[int]

    created_at: datetime
    updated_at: datetime

    status_history: List[OrderStatusHistorySchema]

    model_config = {
        "from_attributes": True
    }


# -----------------------------
# Status Update Schema
# -----------------------------
class OrderStatusUpdate(BaseModel):
    status: str
    updated_by: str  # restaurant admin or delivery partner


# -----------------------------
# Cancel Order Schema
# -----------------------------
class OrderCancel(BaseModel):
    reason: Optional[str] = Field(default="User cancelled the order")
