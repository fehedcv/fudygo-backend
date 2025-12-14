from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.restaurant import Order, OrderStatusHistory
from app.models.user import Profile, Address 
from app.models.restaurant import Restaurant, MenuItem
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    OrderCancel
)
from app.core.auth import get_current_user, check_role, check_any_role
from datetime import datetime
import uuid
from app.realtime.manager import manager
from app.schemas.restaurant import RestaurantOrderResponse


router = APIRouter()


# -------------------------------------------------------
# POST /orders → Place new order
# -------------------------------------------------------
@router.post("/", response_model=OrderResponse)
async def place_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = current_user["db_user"]

    # 1️⃣ Validate restaurant
    restaurant = db.get(Restaurant, order.restaurant_id)
    if not restaurant:
        raise HTTPException(404, "Restaurant not found")

    # 2️⃣ Validate delivery address
    if order.order_type == "delivery":
        address = db.get(Address, order.delivery_address_id)
        if not address or address.profile_id != user.id:
            raise HTTPException(403, "Invalid delivery address")

    # 3️⃣ Validate items
    subtotal = 0
    validated_items = []

    for item_input in order.items:
        menu_item = db.get(MenuItem, item_input.item_id)
        if not menu_item or menu_item.restaurant_id != order.restaurant_id:
            raise HTTPException(400, "Invalid menu item")

        item_total = menu_item.price * item_input.quantity
        subtotal += item_total

        validated_items.append({
            "item_id": menu_item.id,
            "name": menu_item.name,
            "quantity": item_input.quantity,
            "unit_price": menu_item.price,
            "total_price": item_total,
        })

    # 4️⃣ Fees
    delivery_fee = 40 if order.order_type == "delivery" else 0
    tax_amount = int(subtotal * 0.05)
    service_fee = 15
    total_amount = subtotal + delivery_fee + tax_amount + service_fee

    # 5️⃣ Create order
    new_order = Order(
        order_number=f"ORD-{uuid.uuid4().hex[:10].upper()}",
        user_id=user.id,
        restaurant_id=order.restaurant_id,
        delivery_address_id=order.delivery_address_id,
        order_type=order.order_type,
        status="pending",
        scheduled_time=order.scheduled_time,
        items=validated_items,
        subtotal_amount=subtotal,
        delivery_fee=delivery_fee,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_method=order.payment_method,
        special_instructions=order.special_instructions,
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # 6️⃣ Status history
    history = OrderStatusHistory(
        order_id=new_order.id,
        status="pending",
        updated_by=user.full_name,
    )
    db.add(history)
    db.commit()

    # 7️⃣ 🔥 REALTIME PUSH TO POS
    await manager.send_to_restaurant(
        restaurant_id=new_order.restaurant_id,
        payload={
            "type": "NEW_ORDER",
            "order": {
                "id": new_order.id,
                "order_number": new_order.order_number,
                "items": new_order.items,
                "total_amount": new_order.total_amount,
                "order_type": new_order.order_type,
            },
        },
    )

    return new_order


# -------------------------------------------------------
# GET /orders → List all user orders
# -------------------------------------------------------
@router.get("/", response_model=list[OrderResponse])
def list_user_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    orders = db.query(Order).filter(
        Order.user_id == current_user["db_user"].id
    ).order_by(Order.id.desc()).all()

    return orders


# -------------------------------------------------------
# GET /orders/{id} → Order details
# -------------------------------------------------------
@router.get("/{id}", response_model=OrderResponse)
def get_order_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == id).first()

    if not order:
        raise HTTPException(404, "Order not found")

    # User can only access their own order
    if order.user_id != current_user["db_user"].id:
        raise HTTPException(403, "Not your order")

    return order


# -------------------------------------------------------
# PATCH /orders/{id}/status → Restaurant or delivery update
# -------------------------------------------------------
@router.patch("/{id}/status", response_model=OrderResponse)
def update_order_status(
    id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _ = Depends(check_any_role(["manager", "delivery", "admin"]))
):
    order = db.query(Order).filter(Order.id == id).first()

    if not order:
        raise HTTPException(404, "Order not found")

    order.status = data.status
    order.updated_at = datetime.utcnow()

    # Add history
    log = OrderStatusHistory(
        order_id=id,
        status=data.status,
        updated_by=data.updated_by
    )

    db.add(log)
    db.commit()
    db.refresh(order)

    return order


# -------------------------------------------------------
# PATCH /orders/{id}/cancel → User cancel order
# -------------------------------------------------------
@router.patch("/{id}/cancel", response_model=OrderResponse)
def cancel_order(
    id: int,
    data: OrderCancel,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == id).first()

    if not order:
        raise HTTPException(404, "Order not found")

    if order.user_id != current_user["db_user"].id:
        raise HTTPException(403, "You cannot cancel this order")

    if order.status not in ["pending", "accepted"]:
        raise HTTPException(400, "Order cannot be cancelled")

    order.status = "cancelled"

    log = OrderStatusHistory(
        order_id=id,
        status="cancelled",
        updated_by=current_user["db_user"].full_name
    )

    db.add(log)
    db.commit()
    db.refresh(order)

    return order


# -------------------------------------------------------
# GET /orders/{id}/track → Tracking data
# -------------------------------------------------------
@router.get("/{id}/track", response_model=OrderResponse)
def track_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == id).first()

    if not order:
        raise HTTPException(404, "Order not found")

    if order.user_id != current_user["db_user"].id:
        raise HTTPException(403, "Not your order")

    return order


# -------------------------------------------------------
# GET /orders/restaurant/{id} → Restaurant orders
# -------------------------------------------------------
@router.get(
    "/restaurant/{restaurant_id}",
    response_model=list[RestaurantOrderResponse]
)
def get_restaurant_orders(
    restaurant_id: int,
    db: Session = Depends(get_db),
    _ = Depends(check_role("manager"))
):
    orders = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.delivery_address)
        )
        .filter(Order.restaurant_id == restaurant_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders

# -------------------------------------------------------
# GET /orders/delivery/{id} → Delivery partner orders
# -------------------------------------------------------
@router.get("/delivery/{delivery_id}", response_model=list[OrderResponse])
def get_delivery_orders(
    delivery_id: int,
    db: Session = Depends(get_db),
    _ = Depends(check_role("delivery"))
):
    orders = db.query(Order).filter(
        Order.delivery_person_id == delivery_id
    ).all()

    return orders


# -------------------------------------------------------
# DELETE /orders/{id} → Admin delete
# -------------------------------------------------------
@router.delete("/{id}", status_code=204)
def delete_order(
    id: int,
    db: Session = Depends(get_db),
    _ = Depends(check_role("admin"))
):
    order = db.query(Order).filter(Order.id == id).first()

    if not order:
        raise HTTPException(404, "Order not found")

    db.delete(order)
    db.commit()

    return None
