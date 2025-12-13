from fastapi import APIRouter
from app.api.v2 import (
    address,
    menu,
    restaurant,
    users,
    userAuth,
    cart,
    order,
)

router = APIRouter()

router.include_router(userAuth.router, prefix="/auth", tags=["Auth"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(restaurant.router, prefix="/restaurants", tags=["Restaurants"])
router.include_router(address.router, prefix="/addresses", tags=["Addresses"])
router.include_router(menu.router, prefix="/menu", tags=["Menu"])
router.include_router(cart.router, prefix="/cart", tags=["Cart"])
router.include_router(order.router, prefix="/orders", tags=["Orders"])
