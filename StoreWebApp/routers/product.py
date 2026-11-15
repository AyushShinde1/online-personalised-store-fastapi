from fastapi import (APIRouter, Depends, HTTPException, status, Query, Request)
from fastapi.templating import Jinja2Templates
from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Annotated
from decimal import Decimal

from ..database import SessionLocal
from ..models import Product, Store, Category, ProductImage
from .auth import get_current_user

router = APIRouter(
    prefix="/product",
    tags=["product"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class CreateProductRequest(BaseModel):
    id: int | None = None
    # Basic Information
    product_name: str = Field(min_length=1, max_length=200) 
    brand: str | None = Field(default=None, max_length=100)
    sku: str = Field(min_length=1, max_length=100)
    product_description: str = Field(min_length=1)
    main_img_url: str | None = Field(default=None, max_length=2048)
    slug: str | None = None

    # Pricing & Inventory
    mrp: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    product_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    discount_percentage: int | None = Field(default=None, ge=0, le=100)
    # stock_quantity: int = 0
    stock_quantity: int = Field(default = 0, ge=0)
    weight: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=3)
    warrenty_period: str | None = Field(default=None, max_length=100)

    # Ratings & Reviews (This would be update from ProductRatingReview table )
    # product_rating: float = Field(default=0.0, ge=0, le=5) 
    # rating_count: int = Field(default=0, ge=0)
    # review_count: int = Field(default=0, ge=0)

    # Product Settings
    is_active: bool = Field(default=True)
    is_returnable: bool = Field(default=False)

    # Other Information
    storename: str = Field(min_length=1)
    # create_date: datetime | None = None
    # update_date: datetime | None = None

# create seprate rating and review table
class UpdateStockRequest(BaseModel):
    stock_quantity: int = Field(ge=0)


class ProductImageRequest(BaseModel):
    image_url: str = Field(min_length=1, max_length=2048)
    is_primary: bool = False
    display_order: int = Field(default=0, ge=0)


#-------------HELPER FUNCTOINS---------------------


def get_owned_store(db, storename, user):
    if user.get("userrole") != "Business Owner":
        raise HTTPException(
            status_code=403,
            detail="Only business owners can manage products"
        )

    store = db.query(Store).filter(
        Store.storename == storename,
        Store.user_id_fk == user["userid"]
    ).first()

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found or you do not own this store"
        )

    return store


def get_owned_product(db, product_id, user):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    get_owned_store(db, product.store_id_fk, user)

    return product

def product_response(product):

    return {
        "id": product.id,
        "product_name": product.product_name,
        "brand": product.brand,
        "sku": product.sku,
        "product_description": product.product_description,
        "mrp": product.mrp,
        "product_price": product.product_price,
        "discount_percentage": product.discount_percentage,
        "stock_quantity": product.stock_quantity,
        "main_img_url": product.main_img_url,
        "slug": product.slug,
        "weight": product.weight,
        "warrenty_period": product.warrenty_period,
        "product_rating": product.product_rating,
        "rating_count": product.rating_count,
        "review_count": product.review_count,
        "is_active": product.is_active,
        "is_returnable": product.is_returnable,
        "store_id_fk": product.store_id_fk,
        "category_id_fk": product.category_id_fk,
        "create_date": product.create_date,
        "update_date": product.update_date,
        "images": [
            {
                "id": image.id,
                "image_url": image.image_url,
                "is_primary": image.is_primary,
                "display_order": image.display_order
            }
            for image in product.images
        ]
    }



#---------------WEB PAGEs START----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


#---------------WEB PAGEs END  ----------------------------

#-------------------API ROUTERS----------------------
@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_product(request: CreateProductRequest, db: db_dependency, user:user_dependency):
    store = get_owned_store(db, request.storename, user)

    # Validate category
    # if request.category_id_fk is not None:

    #     category = db.query(Category).filter(
    #         Category.id == request.category_id_fk,
    #         Category.is_active == True
    #     ).first()

    #     if not category:
    #         raise HTTPException(
    #             status_code=404,
    #             detail="Category not found or inactive"
    #         )

    # Check SKU uniqueness
    existing_sku = db.query(Product).filter(
        Product.sku == request.sku
    ).first()

    if existing_sku:
        raise HTTPException(
            status_code=409,
            detail="Product SKU already exists"
        )

    if request.product_price > request.mrp:
        raise HTTPException(
            status_code=422,
            detail="Selling price cannot be greater than MRP"
        )

    product_data = request.model_dump(exclude={"id", "storename"})

    product = Product(
        **product_data,
        user_id_fk=user["userid"],
        store_id_fk=store.id
    )

    try:
        db.add(product)
        db.commit()
        db.refresh(product)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product could not be created due to a duplicate or invalid reference"
        )

    return {
        "message": "Product created successfully",
        "product": product_response(product)
    }



#-----------------GET ALL PRODUCTS--------------------------
@router.get("/")
def get_all_products(db: db_dependency, store_id: int | None = None,
                    category_id: int | None = None, search: str | None = None,
                    active_only: bool = True, skip: int = Query(default=0, ge=0),
                    limit: int = Query(default=20, ge=1, le=100)
                    ):

    query = db.query(Product)

    if store_id is not None:
        query = query.filter(Product.store_id_fk == store_id)


    if category_id is not None:
        query = query.filter(Product.category_id_fk == category_id)

    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))

    if active_only:
        query = query.filter(Product.is_active == True)

    total = query.count()

    products = query.order_by(Product.create_date.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "products": [
            product_response(product)
            for product in products
        ]
    }


#-----------------GET SINGLE PRODUCT--------------------------
router.get("/api/{product_id}")
def get_product(product_id: int, db: db_dependency):
    product =  db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product_response(product)


    #Web page
@router.get("/{product_id}")
def product_details_page(
    request: Request,
    product_id: int,
    db: db_dependency,
    user: user_dependency
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    store = db.query(Store).filter(
        Store.id == product.store_id_fk
    ).first()

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )

    # Check whether the logged-in user owns this store
    is_store_owner = (
        user.get("userrole") == "Business Owner"
        and store.user_id_fk == user.get("userid")
    )

    return templates.TemplateResponse(
        request=request,
        name="product_details.html",
        context={
            "product": product,
            "store": store,
            "user": user,
            "is_store_owner": is_store_owner
        }
    )



#-----------------UPDATE PRODUCT--------------------------
class UpdateProductRequest(BaseModel):

    product_name: str | None = Field(default=None, min_length=1, max_length=200)
    brand: str | None = None
    sku: str | None = None
    product_description: str | None = None

    main_img_url: str | None = None
    slug: str | None = None

    mrp: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    product_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)

    discount_percentage: int | None = Field(default=None, ge=0, le=100)
    stock_quantity: int | None = Field(default=None, ge=0)

    weight: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=3)
    warrenty_period: str | None = None

    is_active: bool | None = None
    is_returnable: bool | None = None

    category_id_fk: int | None = None


@router.patch("/{product_id}")
def update_product(product_id: int, request: UpdateProductRequest,
    db: db_dependency, user: user_dependency
):

    product = get_owned_product(db, product_id, user)

    update_data = request.model_dump(exclude_unset=True)

    if "sku" in update_data and update_data["sku"] is not None:

        existing_sku = db.query(Product).filter(
            Product.sku == update_data["sku"],
            Product.id != product_id
        ).first()

        if existing_sku:
            raise HTTPException(
                status_code=409,
                detail="SKU already belongs to another product"
            )

    if "category_id_fk" in update_data:

        category_id = update_data["category_id_fk"]

        if category_id is not None:
            category = db.query(Category).filter(
                Category.id == category_id,
                Category.is_active == True
            ).first()

            if not category:
                raise HTTPException(
                    status_code=404,
                    detail="Category not found or inactive"
                )

    new_mrp = update_data.get("mrp", product.mrp)
    new_price = update_data.get(
        "product_price", product.product_price
    )

    if new_mrp is not None and new_price is not None:
        if new_price > new_mrp:
            raise HTTPException(
                status_code=422,
                detail="Selling price cannot be greater than MRP"
            )

    for key, value in update_data.items():
        setattr(product, key, value)

    try:
        db.commit()
        db.refresh(product)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product update failed due to a duplicate or invalid reference"
        )

    return {
        "message": "Product updated successfully",
        "product": product_response(product)
    }


# ---------------- DELETE PRODUCT ----------------

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: db_dependency,
    user: user_dependency
):

    product = get_owned_product(db, product_id, user)

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully",
        "product_id": product_id
    }


# ---------------- ACTIVATE / DEACTIVATE ----------------

class ProductStatusRequest(BaseModel):
    is_active: bool


@router.patch("/{product_id}/status")
def update_product_status(
    product_id: int,
    request: ProductStatusRequest,
    db: db_dependency,
    user: user_dependency
):

    product = get_owned_product(db, product_id, user)

    product.is_active = request.is_active

    db.commit()

    return {
        "message": "Product status updated",
        "product_id": product.id,
        "is_active": product.is_active
    }


# ---------------- UPDATE STOCK ----------------

@router.patch("/{product_id}/stock")
def update_product_stock(
    product_id: int,
    request: UpdateStockRequest,
    db: db_dependency,
    user: user_dependency
):

    product = get_owned_product(db, product_id, user)

    product.stock_quantity = request.stock_quantity

    db.commit()

    return {
        "message": "Stock updated successfully",
        "product_id": product.id,
        "stock_quantity": product.stock_quantity
    }


# ---------------- ADD PRODUCT IMAGE ----------------

@router.post(
    "/{product_id}/images",
    status_code=status.HTTP_201_CREATED
)
def add_product_image(
    product_id: int,
    request: ProductImageRequest,
    db: db_dependency,
    user: user_dependency
):

    product = get_owned_product(db, product_id, user)

    if request.is_primary:
        for image in product.images:
            image.is_primary = False

    image = ProductImage(
        product_id_fk=product_id,
        image_url=request.image_url,
        is_primary=request.is_primary,
        display_order=request.display_order
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return {
        "message": "Product image added successfully",
        "image_id": image.id,
        "image_url": image.image_url
    }

'''
# ---------------- GET PRODUCT IMAGES ----------------

@router.get("/{product_id}/images")
def get_product_images(
    product_id: int,
    db: db_dependency
):

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return [
        {
            "id": image.id,
            "image_url": image.image_url,
            "is_primary": image.is_primary,
            "display_order": image.display_order
        }
        for image in sorted(
            product.images,
            key=lambda x: x.display_order
        )
    ]



# ---------------- DELETE PRODUCT IMAGE ----------------

@router.delete("/{product_id}/images/{image_id}")
def delete_product_image(
    product_id: int,
    image_id: int,
    db: db_dependency,
    user: user_dependency
):

    product = get_owned_product(db, product_id, user)

    image = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id_fk == product_id
    ).first()

    if not image:
        raise HTTPException(
            status_code=404,
            detail="Product image not found"
        )

    db.delete(image)
    db.commit()

    return {
        "message": "Product image deleted successfully"
    }
'''