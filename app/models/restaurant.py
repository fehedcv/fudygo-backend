from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base


# ---------------------------------------------------------------------
# Utility for UTC timestamps
# ---------------------------------------------------------------------
def utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------
# Restaurant
# ---------------------------------------------------------------------
class Restaurant(Base):
    __tablename__ = 'restaurants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    logo_url = Column(String(255), nullable=True)
    banner_url = Column(String(255), nullable=True)
    address = Column(String(500), nullable=False)
    latitude = Column(String(50), nullable=True, index=True)
    longitude = Column(String(50), nullable=True, index=True)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website_url = Column(String(255), nullable=True)
    operating_hours = Column(String(500), nullable=True)
    is_active = Column(Integer, default=1, index=True)
    minimum_order_amount = Column(Integer, default=0)
    average_delivery_time = Column(Integer, nullable=True)
    average_rating = Column(Integer, default=0)
    total_reviews = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey('profiles.id'), nullable=False, index=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    owner = relationship("Profile", back_populates="restaurants")
    menu_categories = relationship("MenuCategory", order_by="MenuCategory.id",
                                   back_populates="restaurant", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", order_by="MenuItem.id",
                              back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", order_by="Order.id", back_populates="restaurant")
    reviews = relationship("Review", order_by="Review.id", back_populates="restaurant")


# ---------------------------------------------------------------------
# Menu Category
# ---------------------------------------------------------------------
class MenuCategory(Base):
    __tablename__ = 'menu_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    restaurant = relationship("Restaurant", back_populates="menu_categories")
    menu_items = relationship("MenuItem", order_by="MenuItem.id",
                              back_populates="category", cascade="all, delete-orphan")


# ---------------------------------------------------------------------
# Menu Item
# ---------------------------------------------------------------------
class MenuItem(Base):
    __tablename__ = 'menu_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey('menu_categories.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    price = Column(Integer, nullable=False)
    image_url = Column(String(255), nullable=True)
    is_available = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    category = relationship("MenuCategory", back_populates="menu_items")
    restaurant = relationship("Restaurant", back_populates="menu_items")


# ---------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------
class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('profiles.id'), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False, index=True)
    order_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default='pending', index=True)
    delivery_address_id = Column(Integer, ForeignKey('addresses.id'))
    scheduled_time = Column(DateTime, nullable=True)

    items = Column(JSONB, nullable=False)

    subtotal_amount = Column(Integer, nullable=False)
    discount_amount = Column(Integer, default=0)
    delivery_fee = Column(Integer, default=0)
    tax_amount = Column(Integer, default=0)
    total_amount = Column(Integer, nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(String(50), nullable=False, default='unpaid')
    special_instructions = Column(String(1000), nullable=True)
    estimated_delivery_time = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("Profile", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    delivery_address = relationship("Address", back_populates="orders")
    status_history = relationship("OrderStatusHistory", order_by="OrderStatusHistory.id",
                                  back_populates="order", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="order")


# ---------------------------------------------------------------------
# Order Status History
# ---------------------------------------------------------------------
class OrderStatusHistory(Base):
    __tablename__ = 'order_status_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    updated_by = Column(String(255), nullable=False)

    timestamp = Column(DateTime, default=utcnow, index=True)

    order = relationship("Order", back_populates="status_history")


# ---------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------
class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('profiles.id'), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    rating = Column(Integer, nullable=False, index=True)
    review_text = Column(String(2000), nullable=True)

    created_at = Column(DateTime, default=utcnow, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("Profile", back_populates="reviews")
    restaurant = relationship("Restaurant", back_populates="reviews")
    order = relationship("Order", back_populates="reviews", uselist=False)


# ---------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------
class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('profiles.id'), nullable=False, index=True)
    total_amount = Column(Integer, nullable=False)
    total_items = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("Profile", back_populates="cart")
    items = relationship("CartItem", order_by="CartItem.id",
                         back_populates="cart", cascade="all, delete-orphan")


# ---------------------------------------------------------------------
# Cart Item
# ---------------------------------------------------------------------
class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey('carts.id', ondelete="CASCADE"), nullable=False, index=True)
    menu_item_id = Column(Integer, ForeignKey('menu_items.id', ondelete="CASCADE"), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id', ondelete="CASCADE"), nullable=False, index=True)

    quantity = Column(Integer, nullable=False, default=1)
    price_per_item = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    notes = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=utcnow)

    cart = relationship("Cart", back_populates="items")
    menu_item = relationship("MenuItem")
    restaurant = relationship("Restaurant")

    __table_args__ = (
        UniqueConstraint('cart_id', 'menu_item_id', 'restaurant_id', name='unique_cart_item'),
    )
