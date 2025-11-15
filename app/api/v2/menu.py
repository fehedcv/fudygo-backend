from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.restaurant import MenuItem, MenuCategory
from app.schemas.menu import (
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    MenuCategoryResponse,
)
from app.core.auth import (
    get_current_user,
    check_any_role,
)

router = APIRouter()



# Dependency wrapper for manager/admin role
def ManagerOrAdmin():
    return check_any_role(["manager", "admin"])


# ===========================================================================
# PUBLIC ENDPOINTS
# ===========================================================================

@router.get(
    "/restaurants/{restaurant_id}",
    response_model=list[MenuItemResponse],
    summary="Get menu for a restaurant",
)
def get_menu_for_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
):
    items = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()
    return items


@router.get(
    "/{item_id}",
    response_model=MenuItemResponse,
    summary="Get menu item details",
)
def get_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Menu item not found")
    return item


@router.get(
    "/categories",
    response_model=list[MenuCategoryResponse],
    summary="Get global menu categories",
)
def get_global_categories(
    db: Session = Depends(get_db),
):
    return db.query(MenuCategory).all()


# ===========================================================================
# PROTECTED ENDPOINTS (manager or admin)
# ===========================================================================

@router.post(
    "/restaurants/{restaurant_id}",
    response_model=MenuItemResponse,
    status_code=201,
    summary="Add new menu item",
)
def add_menu_item(
    restaurant_id: int,
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    _ = Depends(ManagerOrAdmin),  # auth applied here
):
    if item.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=400,
            detail="restaurant_id mismatch between URL and body",
        )

    new_item = MenuItem(**item.dict())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.put(
    "/{item_id}",
    response_model=MenuItemResponse,
    summary="Update full menu item",
)
def update_menu_item(
    item_id: int,
    payload: MenuItemCreate,
    db: Session = Depends(get_db),
    _ = Depends(ManagerOrAdmin),
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Menu item not found")

    for key, value in payload.dict().items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@router.patch(
    "/{item_id}",
    response_model=MenuItemResponse,
    summary="Partially update menu item",
)
def patch_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    db: Session = Depends(get_db),
    _ = Depends(ManagerOrAdmin),
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Menu item not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/{item_id}",
    status_code=204,
    summary="Delete menu item",
)
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    _ = Depends(ManagerOrAdmin),
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Menu item not found")

    db.delete(item)
    db.commit()
    return
