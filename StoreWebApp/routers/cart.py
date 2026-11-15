from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Annotated


from .. import models
from ..database import  SessionLocal
from .auth import get_current_user
from .auth import require_login_redirect


from fastapi import Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


@router.get("/page")
def cart_page(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    return templates.TemplateResponse(
        request=request,
        name="cart.html"
    )



@router.post("/add/{product_id}")
def add_to_cart(
    db: db_dependency,
    product_id: int,
    quantity: int = 1,
    current_user: dict = Depends(require_login_redirect) 
):
    if quantity <= 0:
        raise HTTPException(400, "Quantity must be greater than zero")

    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(404, "Product not found")

    if product.stock_quantity < quantity:
        raise HTTPException(400, "Insufficient stock")

    cart_item = db.query(models.CartItem).filter(
        models.CartItem.user_id_fk == current_user["userid"],
        models.CartItem.product_id_fk == product_id
    ).first()

    if cart_item:
        new_quantity = cart_item.quantity + quantity

        if new_quantity > product.stock_quantity:
            raise HTTPException(400, "Insufficient stock")

        cart_item.quantity = new_quantity

    else:
        cart_item = models.CartItem(
            user_id_fk=current_user["userid"],
            product_id_fk=product_id,
            quantity=quantity
        )

        db.add(cart_item)

    db.commit()
    db.refresh(cart_item)

    return {
        "message": "Product added to cart",
        "cart_item_id": cart_item.id,
        "quantity": cart_item.quantity
    }


@router.get("/")
def get_cart(
    db: db_dependency,
    current_user: dict = Depends(require_login_redirect)
):
    cart_items = db.query(models.CartItem).options(
        joinedload(models.CartItem.product)
    ).filter(
        models.CartItem.user_id_fk == current_user["userid"]
    ).all()

    result = []

    for item in cart_items:
        product = item.product

        result.append({
            "cart_item_id": item.id,
            "product_id": product.id,
            "product_name": product.product_name,
            "product_image": product.main_img_url,
            "price": product.product_price,
            "quantity": item.quantity,
            "subtotal": float(product.product_price * item.quantity)
        })

    return {
        "items": result,
        "total_items": sum(item.quantity for item in cart_items),
        "total_price": sum(
            float(item.product.product_price * item.quantity)
            for item in cart_items
        )
    }


@router.put("/update/{cart_item_id}")
def update_cart_item(
    cart_item_id: int,
    quantity: int,
    db: db_dependency,
    current_user: dict = Depends(require_login_redirect)
):
    if quantity <= 0:
        raise HTTPException(400, "Quantity must be greater than zero")

    item = db.query(models.CartItem).filter(
        models.CartItem.id == cart_item_id,
        models.CartItem.user_id_fk == current_user["userid"]
    ).first()

    if not item:
        raise HTTPException(404, "Cart item not found")

    if quantity > item.product.stock_quantity:
        raise HTTPException(400, "Insufficient stock")

    item.quantity = quantity

    db.commit()

    return {"message": "Cart updated successfully"}


@router.delete("/remove/{cart_item_id}")
def remove_cart_item(
    cart_item_id: int,
    db: db_dependency,
    current_user: dict = Depends(require_login_redirect)
):
    item = db.query(models.CartItem).filter(
        models.CartItem.id == cart_item_id,
        models.CartItem.user_id_fk == current_user["userid"]
    ).first()

    if not item:
        raise HTTPException(404, "Cart item not found")

    db.delete(item)
    db.commit()

    return {"message": "Product removed from cart"}


@router.delete("/clear")
def clear_cart(
    db: db_dependency,
    current_user: dict = Depends(require_login_redirect)
):
    db.query(models.CartItem).filter(
        models.CartItem.user_id_fk == current_user["userid"]
    ).delete(synchronize_session=False)

    db.commit()

    return {"message": "Cart cleared successfully"}
