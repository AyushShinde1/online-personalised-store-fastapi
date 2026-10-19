from sqlalchemy import Column, String, Integer, Boolean

from .database import Base

class Users(Base):
    __tablename__ = 'users'

    id=Column(Integer, primary_key=True, index=True)
    username=Column(String, unique=True, nullable=False, index=True)
    password=Column(String, nullable=False)
    first_name=Column(String, nullable=False)
    last_name=Column(String)
    hashed_password=Column(String, nullable=False)
    role=Column(String, nullable=False, default="user")
    is_active=Column(Boolean,nullable=False, default=True)
    phone_number=Column(String,nullable=False)
    email=Column(String)