from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.restaurant import Restaurant as RestaurantModel
from app.schemas.restaurant import Restaurant
from app.core.auth import get_current_user,check_role
from app.schemas.menu import MenuCategory, MenuCategoryCreate, MenuItem, MenuItemCreate,MenuItemUpdate

router = APIRouter()


#get menu for restaurant
@router.get("/restaurants/{restaurant_id}/menu/", response_model=list[MenuItem], description="Get menu items for a specific restaurant")
def get_menu_for_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()
    return menu_items


@router.post("/menu-items/", response_model=MenuItem, description="Create a new menu item (manager or admin only)")
def create_menu_item(
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_role("manager", current_user, db) or check_role("admin", current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized as manager")
    
    db_item = MenuItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


#get menu item details
@router.get("/menu-items/{item_id}/", response_model=MenuItem, description="Get details of a specific menu item")
def get_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return db_item


#put menu item (manager or admin only)
@router.put("/menu-items/{item_id}/", response_model=MenuItem, description="Update a menu item (manager or admin only)")
def update_menu_item(
    item_id: int,
    item_update: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_role("manager", current_user, db) or check_role("admin", current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized as manager")
    
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    for key, value in item_update.dict(exclude_unset=True).items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


#patch menu item (manager or admin only)
@router.patch("/menu-items/{item_id}/", response_model=MenuItem, description="Partially update a menu item (manager or admin only)")
def patch_menu_item(
    item_id: int,
    item_update: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_role("manager", current_user, db) or check_role("admin", current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized as manager")
    
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    for key, value in item_update.dict(exclude_unset=True).items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


#delete menu item (manager or admin only)
@router.delete("/menu-items/{item_id}/", status_code=status.HTTP_204_NO_CONTENT, description="Delete a menu item (manager or admin only)")
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not check_role("manager", current_user, db) or check_role("admin", current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized as manager")
    
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    db.delete(db_item)
    db.commit()
    return "deleted successfully"


#get global categories
@router.get("/categories/", response_model=list[MenuCategory], description="Get all menu categories")
def get_menu_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    categories = db.query(MenuCategory).all()
    return categories


