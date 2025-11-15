from app.schemas.orders import OrderCreate,OrderStatusUpdate
from app.schemas.cart import CartResponse, CartItemBase, CartItemResponse, CartItemUpdate   
from app.models.restaurant import Order,OrderStatusHistory
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user,check_any_role
from typing import List

router = APIRouter()


#place an order by user
@router.post("/", response_model=OrderCreate)
def place_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Create a new order
    new_order = Order(**order.model_dump(), user_id=current_user["user_id"])
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

#get orders placed by user me
@router.get("/me", response_model=List[OrderCreate])
def get_orders_for_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    orders = db.query(Order).filter(Order.user_id == current_user["user_id"]).all()
    return orders


#get order details
@router.get("/{order_id}", response_model=OrderCreate)
def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user["user_id"]).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

#update Order status by admin or manager
@router.patch("/{order_id}/status", response_model=OrderStatusUpdate)
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_any_role(["admin", "manager"], current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized as admin or manager")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return HTTPException(status_code=404, detail="Order not found")


    #update status
    order.status = status_update.status
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

#cancel order by user
@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.user_id == current_user["user_id"], Order.id == order_id).first()
    if not order:
        return HTTPException(status_code=404, detail="Order not found")
    
    db.delete(order)
    db.commit()
    return None


