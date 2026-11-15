
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Annotated

from .. import models
from ..database import  SessionLocal
from .auth import get_current_user, require_login_redirect

router = APIRouter(
    prefix="/reviews",
    tags=["Product Reviews"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/{product_id}")
def add_review(
    product_id: int,
    rating: float,
    review: str,
    db: db_dependency,
    current_user: dict = Depends(require_login_redirect)
):
    # Check whether the customer purchased this product
    purchased_product = db.query(
        models.OrderItem
    ).join(
        models.Order,
        models.Order.id == models.OrderItem.order_id_fk
    ).filter(
        models.Order.user_id_fk == current_user["userid"],
        models.OrderItem.product_id_fk == product_id,
        models.Order.status == "delivered"
    ).first()
    
    if not purchased_product:
        raise HTTPException(
            status_code=403,
            detail="You can review this product only after purchasing and receiving it"
        )
    
    if not 1 <= rating <= 5:
        raise HTTPException(400, "Rating must be between 1 and 5")

    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(404, "Product not found")

    existing_review = db.query(
        models.ProductRatingReview
    ).filter(
        models.ProductRatingReview.product_id_fk == product_id,
        models.ProductRatingReview.user_id_fk == current_user["userid"]
    ).first()

    if existing_review:
        raise HTTPException(
            400,
            "You have already reviewed this product"
        )

    new_review = models.ProductRatingReview(
        rating=rating,
        review=review,
        product_id_fk=product_id,
        user_id_fk=current_user.id
    )

    db.add(new_review)
    db.flush()

    update_product_rating(db, product)

    db.commit()

    return {"message": "Review submitted successfully"}


@router.get("/{product_id}")
def get_product_reviews(
    product_id: int,
    db: db_dependency
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(404, "Product not found")

    reviews = db.query(
        models.ProductRatingReview
    ).filter(
        models.ProductRatingReview.product_id_fk == product_id
    ).all()

    return {
        "product_id": product_id,
        "average_rating": product.product_rating,
        "rating_count": product.rating_count,
        "reviews": [
            {
                "id": r.id,
                "rating": r.rating,
                "review": r.review,
                "username": r.user.username
            }
            for r in reviews
        ]
    }


@router.put("/{review_id}")
def update_review(
    review_id: int,
    rating: float,
    review: str,
    db: db_dependency,
    current_user: dict = Depends(require_login_redirect)
):
    if not 1 <= rating <= 5:
        raise HTTPException(400, "Rating must be between 1 and 5")

    existing_review = db.query(
        models.ProductRatingReview
    ).filter(
        models.ProductRatingReview.id == review_id,
        models.ProductRatingReview.user_id_fk == current_user["userid"]
    ).first()

    if not existing_review:
        raise HTTPException(404, "Review not found")

    existing_review.rating = rating
    existing_review.review = review

    update_product_rating(db, existing_review.product)

    db.commit()

    return {"message": "Review updated successfully"}


@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: db_dependency,
    current_user: dict = Depends(require_login_redirect)
):
    existing_review = db.query(
        models.ProductRatingReview
    ).filter(
        models.ProductRatingReview.id == review_id,
        models.ProductRatingReview.user_id_fk == current_user["userid"]
    ).first()

    if not existing_review:
        raise HTTPException(404, "Review not found")

    product = existing_review.product

    db.delete(existing_review)
    db.flush()

    update_product_rating(db, product)

    db.commit()

    return {"message": "Review deleted successfully"}


def update_product_rating(db, product):

    result = db.query(
        func.avg(models.ProductRatingReview.rating),
        func.count(models.ProductRatingReview.id)
    ).filter(
        models.ProductRatingReview.product_id_fk == product.id
    ).first()

    product.product_rating = float(result[0] or 0)
    product.rating_count = result[1] or 0
    product.review_count = result[1] or 0
