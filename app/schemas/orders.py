from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class OrderCreate(BaseModel):
    order_number: str
    user_id: int
    restaurant_id: int
    order_type: str
    status: str
    delivery_address_id: int
    scheduled_time: Optional[datetime] = None
    items: List[dict]
    subtotal_amount: int
    discount_amount: int = 0
    delivery_fee: int = 0
    tax_amount: int = 0
    total_amount: int
    payment_method: str
    payment_status: str
    special_instructions: Optional[str] = None
    estimated_delivery_time: Optional[int] = None

    class Config:
        orm_mode = True

class OrderStatusUpdate(BaseModel):
    status: str

    class Config:
        orm_mode = True

class OrderStatusHistoryBase(BaseModel):
    order_id: int
    status: str
    updated_by: str

    class Config:
        orm_mode = True

class OrderStatusHistory(OrderStatusHistoryBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class Order(OrderCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    status_history: List[OrderStatusHistory] = []

    class Config:
        orm_mode = True

