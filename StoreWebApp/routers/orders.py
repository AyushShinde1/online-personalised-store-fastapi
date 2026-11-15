
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Annotated
from decimal import Decimal

from ..database import SessionLocal
from .. import models
from .auth import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/checkout")
def checkout(
    db: db_dependency,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["userid"]

    try:
        cart_items = db.query(models.CartItem).options(
            joinedload(models.CartItem.product)
        ).filter(
            models.CartItem.user_id_fk == user_id
        ).with_for_update().all()

        if not cart_items:
            raise HTTPException(400, "Your cart is empty")

        total = Decimal("0.00")

        for item in cart_items:
            product = item.product

            if not product.is_active:
                raise HTTPException(
                    400,
                    f"{product.product_name} is unavailable"
                )

            if item.quantity > product.stock_quantity:
                raise HTTPException(
                    400,
                    f"Insufficient stock for {product.product_name}"
                )

            total += product.product_price * item.quantity

        order = models.Order(
            user_id_fk=user_id,
            total_amount=total,
            status="pending"
        )

        db.add(order)
        db.flush()

        for item in cart_items:
            order_item = models.OrderItem(
                order_id_fk=order.id,
                product_id_fk=item.product_id_fk,
                quantity=item.quantity,
                purchase_price=item.product.product_price
            )

            db.add(order_item)

        db.commit()
        db.refresh(order)

        return {
            "message": "Order created successfully",
            "order_id": order.id,
            "total_amount": float(order.total_amount),
            "status": order.status
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            500,
            "Unable to create order"
        )


@router.get("/")
def get_my_orders(
    db: db_dependency,
    current_user: dict = Depends(get_current_user)
):
    orders = db.query(models.Order).options(
        joinedload(models.Order.items)
    ).filter(
        models.Order.user_id_fk == current_user["userid"]
    ).order_by(
        models.Order.create_date.desc()
    ).all()

    return [
        {
            "order_id": order.id,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "items": [
                {
                    "product_id": item.product_id_fk,
                    "product_name": item.product.product_name,
                    "quantity": item.quantity,
                    "purchase_price": float(item.purchase_price)
                }
                for item in order.items
            ]
        }
        for order in orders
    ]
