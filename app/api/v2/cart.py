from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.restaurant import Cart, CartItem
from app.schemas.cart import CartItemBase, CartItemResponse, CartResponse, CartItemUpdate
from app.core.auth import get_current_user

router = APIRouter()

@router.get("/me", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart = db.query(Cart).filter(Cart.user_id == current_user["user_id"]).first()
    if not cart:
        cart = Cart(user_id=current_user["user_id"])
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.post("/items", response_model=CartResponse)
def add_item_to_cart(
    item: CartItemBase,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart = db.query(Cart).filter(Cart.user_id == current_user["user_id"]).first()
    if not cart:
        cart = Cart(user_id=current_user["user_id"])
        db.add(cart)
        db.commit()
        db.refresh(cart)

    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.menu_item_id == item.menu_item_id,
        CartItem.restaurant_id == item.restaurant_id
    ).first()

    if existing_item:
        existing_item.quantity += item.quantity
        existing_item.price_per_item = item.price_per_item
        existing_item.total_price = item.total_price
        existing_item.notes = item.notes
    else:
        new_item = CartItem(**item.model_dump(), cart_id=cart.id)
        db.add(new_item)

    #recalculate totals
    cart.total_price = sum(item.total_price for item in cart.items)
    cart.total_items = sum(item.quantity for item in cart.items)

    db.commit()
    db.refresh(cart)
    return cart 

@router.patch("/items/{item_id}", response_model=CartResponse)
def update_item_in_cart(
    item_id: int,
    item_update: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart = db.query(Cart).filter(Cart.user_id == current_user["user_id"]).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    cart_item.quantity = item_update.quantity
    cart_item.notes = item_update.notes
    
    cart.total_items = sum(item.quantity for item in cart.items)
    cart.total_amount = sum(item.total_price for item in cart.items)
    
    db.commit()
    db.refresh(cart)
    return cart

@router.delete("/items/{item_id}", response_model=CartResponse)
def remove_item_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart = db.query(Cart).filter(Cart.user_id == current_user["user_id"]).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(item)
    db.commit()

    cart.total_amount = sum(item.total_price for item in cart.items)
    cart.total_items = sum(item.quantity for item in cart.items)
    
    return cart


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None
)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart = db.query(Cart).filter(Cart.user_id == current_user["user_id"]).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    db.delete(cart)
    db.commit()
