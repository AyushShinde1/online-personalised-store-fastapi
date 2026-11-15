
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated


from .. import models
from ..database import  SessionLocal
from .auth import get_current_user

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/")
def get_categories(db: db_dependency):

    categories = db.query(models.Category).filter(
        models.Category.is_active == True
    ).all()

    return [
        {
            "id": c.id,
            "category_name": c.category_name,
            "description": c.description,
            "parent_category_id": c.parent_category_id_fk
        }
        for c in categories
    ]


@router.get("/{category_id}")
def get_category(
    category_id: int,
    db: db_dependency
):

    category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.is_active == True
    ).first()

    if not category:
        raise HTTPException(404, "Category not found")

    return {
        "id": category.id,
        "category_name": category.category_name,
        "description": category.description,
        "parent_category_id": category.parent_category_id_fk
    }


@router.post("/")
def create_category(
    db: db_dependency,
    category_name: str,
    description: str = None,
    parent_category_id: int = None,
    current_user: models.Users = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(403, "Only admins can create categories")

    if parent_category_id is not None:
        parent = db.query(models.Category).filter(
            models.Category.id == parent_category_id,
            models.Category.is_active == True
        ).first()

        if not parent:
            raise HTTPException(404, "Parent category not found")

    category = models.Category(
        category_name=category_name,
        description=description,
        parent_category_id_fk=parent_category_id
    )

    db.add(category)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(400, "Category name already exists")

    db.refresh(category)

    return {
        "message": "Category created successfully",
        "category_id": category.id
    }


@router.put("/{category_id}")
def update_category(
    db: db_dependency,
    category_id: int,
    category_name: str,
    description: str = None,
    current_user: models.Users = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(403, "Only admins can update categories")

    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(404, "Category not found")

    category.category_name = category_name
    category.description = description

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(400, "Category name already exists")

    return {"message": "Category updated successfully"}


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: db_dependency,
    current_user: models.Users = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(403, "Only admins can delete categories")

    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(404, "Category not found")

    category.is_active = False

    db.commit()

    return {"message": "Category deactivated successfully"}
