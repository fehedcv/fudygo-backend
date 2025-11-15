from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.restaurant import Cart, CartItem, MenuItem, Restaurant
from app.core.auth import get_current_user
from app.schemas.cart import (
    CartResponse, CartItemCreate, CartItemUpdate, CartItemResponse
)

router = APIRouter()



# ─────────────────────────────────────────────
# Helper — get or create cart
# ─────────────────────────────────────────────
def get_or_create_cart(db, user_id):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(
            user_id=user_id,
            total_amount=0,
            total_items=0
        )
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def recalc_cart(cart):
    cart.total_items = sum(item.quantity for item in cart.items)
    cart.total_amount = sum(item.total_price for item in cart.items)


@router.get("/me", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart = get_or_create_cart(db, current_user["db_user"].id)
    return cart


@router.post("/items", response_model=CartItemResponse)
def add_item(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["db_user"].id
    cart = get_or_create_cart(db, user_id)

    menu_item = db.query(MenuItem).filter(MenuItem.id == item.menu_item_id).first()
    if not menu_item:
        raise HTTPException(404, "Menu item not found")

    # Check if item already exists in the cart
    existing = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.menu_item_id == item.menu_item_id,
        CartItem.restaurant_id == item.restaurant_id
    ).first()

    if existing:
        # Increase quantity
        existing.quantity += item.quantity
        existing.total_price = existing.quantity * existing.price_per_item
        recalc_cart(cart)
        db.commit()
        db.refresh(existing)
        return existing

    # Create new cart item
    cart_item = CartItem(
        cart_id=cart.id,
        menu_item_id=item.menu_item_id,
        restaurant_id=item.restaurant_id,
        quantity=item.quantity,
        price_per_item=menu_item.price,
        total_price=menu_item.price * item.quantity,
        notes=item.notes
    )

    db.add(cart_item)
    recalc_cart(cart)
    db.commit()
    db.refresh(cart_item)

    return cart_item


@router.patch("/items/{item_id}", response_model=CartItemResponse)
def update_item(
    item_id: int,
    body: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart_item = db.query(CartItem).join(Cart).filter(
        Cart.user_id == current_user["db_user"].id,
        CartItem.id == item_id
    ).first()

    if not cart_item:
        raise HTTPException(404, "Item not found in your cart")

    if body.quantity <= 0:
        raise HTTPException(400, "Quantity must be at least 1")

    cart_item.quantity = body.quantity
    cart_item.total_price = cart_item.quantity * cart_item.price_per_item

    recalc_cart(cart_item.cart)
    db.commit()
    db.refresh(cart_item)

    return cart_item


@router.delete("/items/{item_id}", status_code=204)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart_item = db.query(CartItem).join(Cart).filter(
        Cart.user_id == current_user["db_user"].id,
        CartItem.id == item_id
    ).first()

    if not cart_item:
        raise HTTPException(404, "Item not found")

    cart = cart_item.cart
    db.delete(cart_item)
    recalc_cart(cart)

    db.commit()
    return None


@router.delete("", status_code=204)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart = db.query(Cart).filter(Cart.user_id == current_user["db_user"].id).first()

    if not cart:
        raise HTTPException(404, "Cart not found")

    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

    cart.total_amount = 0
    cart.total_items = 0

    db.commit()
    return None
