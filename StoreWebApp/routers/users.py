from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Annotated
from sqlalchemy.orm import Session
from collections.abc import Generator

import re

from ..models import Users
from ..database import SessionLocal
from ..security import hash_password, verify_password

router = APIRouter(
    prefix='/users',
    tags=['users']
)


def get_db() -> Generator[Session, None, None]:
    '''Create a database session and close it after usse.'''
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

'''Function uses yield, not return. That makes it a generator function, so Generator[Session, None, None] is a more accurate return type hint.'''        

db_dependency = Annotated[Session, Depends(get_db)]

class CreateUserRequest(BaseModel):
    id: int | None = None
    username: str = Field(min_length=6, max_length=50)
    password: str
    first_name: str
    last_name: str
    role: str | None = None
    # phone_number: str = Field(pattern=r"^\d{10}$")
    phone_number: str
    email: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password:str) -> str:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValueError("Password must contain at least one special character")
        return password

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits.")
        return value


@router.post('/create-user', status_code=status.HTTP_201_CREATED)
def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    user = db.query(Users).filter(create_user_request.username == Users.username).first()

    if user:
        raise HTTPException(status_code=401, detail="User already exists")
    
    # Hash the password
    hashed_password = hash_password(create_user_request.password)

    # Create a SQLAlchemy model instance
    create_user_model = Users(
        username=create_user_request.username,
        password=create_user_request.password,#Adding temporarily
        hashed_password=hashed_password,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        # role=create_user_request.role,
        phone_number=create_user_request.phone_number,
        email=create_user_request.email
    )
    verify = verify_password(create_user_request.password,hashed_password)

    db.add(create_user_model)
    db.commit()

    return {'verified_password':verify}


@router.put('/update-user', status_code=status.HTTP_204_NO_CONTENT)
def update_user(db: db_dependency, update_user_request:CreateUserRequest):
    user = db.query(Users).filter(update_user_request.id == Users.id).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User Not Found!")

    user.username=update_user_request.username
    # user.password=update_user_request.password,#Adding temporarily
    # user.hashed_password=update_password
    user.first_name=update_user_request.first_name
    user.last_name=update_user_request.last_name
    user.role=user.role
    user.phone_number=update_user_request.phone_number
    user.email=update_user_request.email

    db.add(user)
    db.commit()







