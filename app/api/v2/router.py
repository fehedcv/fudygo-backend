from fastapi import FastAPI
from app.api.v2 import (
    address,menu,restaurant,users,userAuth,cart,order
)

app = FastAPI(
    title="FudyGo Backend API",
    description="API for a food delivery service.",
    version="2.0.0"
)

app.include_router(userAuth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(restaurant.router, prefix="/restaurants", tags=["Restaurants"])
app.include_router(address.router, prefix="/addresses", tags=["Addresses"])
app.include_router(menu.router, prefix="/menu", tags=["Menu"])
app.include_router(cart.router, prefix="/cart", tags=["Cart"])
app.include_router(order.router, prefix="/orders", tags=["Orders"])

