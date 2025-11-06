#to create a profile table in sqlalchemy postgresql
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
import datetime
from app.db.base import Base

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

class Profile(Base):
    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)  # You can convert this to UUID later
    firebase_uid = Column(String(128), unique=True, nullable=True, index=True)  # Firebase user UID
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Optional (since Firebase handles auth)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True, index=True)
    profile_picture_url = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)
    is_verified = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    addresses = relationship("Address", order_by="Address.id", back_populates="profile", cascade="all, delete-orphan")
    restaurants = relationship("Restaurant", order_by="Restaurant.id", back_populates="owner")
    orders = relationship("Order", order_by="Order.id", back_populates="user")
    reviews = relationship("Review", order_by="Review.id", back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)  # e.g. 'admin', 'client', 'manager'
    description = Column(String(255), nullable=True)

    users = relationship("Profile", secondary=user_roles, back_populates="roles")

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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    
    profile = relationship("Profile", back_populates="addresses")
    orders = relationship("Order", order_by="Order.id", back_populates="delivery_address")
