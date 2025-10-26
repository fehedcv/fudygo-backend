#to create a profile table in sqlalchemy postgresql
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime


Base = declarative_base()

class Profile(Base):
    __tablename__ = 'profiles'
     
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    profile__picture_url = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default='user')
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    is_verified = Column(Integer, default=0)  # 1 for verified, 0 for not verified
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    addresses = relationship("Address", order_by="Address.id", back_populates="profile", cascade="all, delete-orphan")
    restaurants = relationship("Restaurant", order_by="Restaurant.id", back_populates="owner")
    orders = relationship("Order", order_by="Order.id", back_populates="user")
    reviews = relationship("Review", order_by="Review.id", back_populates="user")

class Address(Base):
    __tablename__ = 'addresses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('profiles.id'), nullable=False)
    label = Column(String(50), nullable=False)  # e.g., Home, Work
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    post_code = Column(String(20), nullable=False)
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    is_default = Column(Integer, default=0)  # 1 for default address, 0 otherwise
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    

    profile = relationship("Profile", back_populates="addresses")
    orders = relationship("Order", order_by="Order.id", back_populates="delivery_address")
