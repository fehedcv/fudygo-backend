from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base



class Profile(Base):
    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)  # You can convert this to UUID later
    firebase_uid = Column(String(128), unique=True, nullable=True, index=True)  # Firebase user UID
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Optional (since Firebase handles auth)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True, index=True)
    profile_picture_url = Column(String(255), nullable=True)

    # ✅ Roles stored directly as a PostgreSQL string array
    roles = Column(ARRAY(String), nullable=False, default=['user'])

    is_active = Column(Integer, default=1)
    is_verified = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    addresses = relationship(
        "Address",
        order_by="Address.id",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    restaurants = relationship(
        "Restaurant",
        order_by="Restaurant.id",
        back_populates="owner"
    )
    orders = relationship(
        "Order",
        order_by="Order.id",
        back_populates="user"
    )
    reviews = relationship(
        "Review",
        order_by="Review.id",
        back_populates="user"
    )


class Address(Base):
    __tablename__ = 'addresses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('profiles.id'), nullable=False, index=True)
    label = Column(String(50), nullable=False)  # e.g., Home, Work
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    post_code = Column(String(20), nullable=False, index=True)
    latitude = Column(String(50), nullable=True, index=True)
    longitude = Column(String(50), nullable=True, index=True)
    is_default = Column(Integer, default=0)  # 1 for default address, 0 otherwise
    created_at = Column(DateTime, default=datetime.utcnow)
    

    profile = relationship("Profile", back_populates="addresses")
    orders = relationship("Order", order_by="Order.id", back_populates="delivery_address")
