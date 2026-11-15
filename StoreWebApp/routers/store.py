from fastapi import APIRouter, status, Depends, Request, HTTPException, Path, Query, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse

from pathlib import Path as FilePath

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Annotated
from sqlalchemy.orm import Session, joinedload

from jwt.exceptions import InvalidTokenError

from ..database import SessionLocal, blacklisted_tokens
from ..models import Store, Product
from .auth import decode_access_token, get_current_user
from .auth import require_login_redirect


from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from sqlalchemy.orm import Session, joinedload
from ..models import Store, Product

router = APIRouter(
    prefix='/store',
    tags=['store']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

security = HTTPBearer(auto_error=False)

class CreateStoreRequest(BaseModel):
    id: int | None = None
    storename: str = Field(min_length=1)
    store_description: str
    store_dp_path: str
    store_background_img_path: str
    create_date: datetime | None = None
    update_data: datetime | None = None

def serialize_product(product):

    return {
        "id": product.id,
        "product_name": product.product_name,
        "brand": product.brand,
        "sku": product.sku,
        "product_description": product.product_description,

        "mrp": float(product.mrp),
        "product_price": float(product.product_price),

        "discount_percentage": product.discount_percentage,
        "stock_quantity": product.stock_quantity,

        "main_img_url": product.main_img_url,

        "product_rating": product.product_rating,
        "rating_count": product.rating_count,
        "review_count": product.review_count,

        "is_active": product.is_active,
        "is_returnable": product.is_returnable,

        "store_id_fk": product.store_id_fk,
        "category_id_fk": product.category_id_fk,

        "images": [
            {
                "id": image.id,
                "image_url": image.image_url,
                "is_primary": image.is_primary,
                "display_order": image.display_order
            }
            for image in product.images
        ],

        "category": (
            {
                "id": product.category.id,
                "category_name": product.category.category_name
            }
            if product.category else None
        )
    }


def serialize_store(store):

    return {
        "id": store.id,
        "storename": store.storename,
        "store_description": store.store_description,
        "store_dp_path": store.store_dp_path,
        "store_background_img_path": store.store_background_img_path,
        "user_id_fk": store.user_id_fk
    }

#---------------HELPER FUNCTIONS START---------------------    
def get_owned_store(db, storename, user):
    # if user.get("userrole") != "Business Owner":
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Only business owners can manage products"
    #     )

    store = db.query(Store).filter(
        Store.storename == storename,
        # Store.user_id_fk == user["userid"]
    ).first()

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found."
        )

    return store

#---------------HELPER FUNCTIONS END  ---------------------    

BASE_DIR = FilePath(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))




@router.post('/create-store', status_code=status.HTTP_201_CREATED)
def create_store(db: db_dependency, create_store_request: CreateStoreRequest, payload: user_dependency):
    '''
    #this can be replaced by get_current_user
    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    jti = payload.get("jti")

    if not jti:
        raise HTTPException(status_code=401, details="Token ID missing")

    if jti in blacklisted_tokens:
        raise HTTPException(status_code=401, details="Token has been revoked")
    '''

    userrole = payload.get('userrole')

    if userrole != "Business Owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only business owners can create stores")

    user_id = payload.get("userid")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID missing from token",
        )

    store = Store(
        storename=create_store_request.storename,
        store_description=create_store_request.store_description,
        store_dp_path=create_store_request.store_dp_path,
        store_background_img_path=(
            create_store_request.store_background_img_path
        ),
        user_id_fk=user_id,
        create_date=datetime.now (timezone.utc),
        update_date=datetime.now (timezone.utc),
    )

    try:
        db.add(store)
        db.commit()
        db.refresh(store)
    except Exception:
        db.rollback()
        raise


    return {
        "message": "Store created successfully",
        "store_id": store.id,
        "storename": store.storename,
    }




@router.get("/api")
def get_all_store_products(
    db: db_dependency,
    payload: user_dependency,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100)
):

    query = db.query(Product).options(
        joinedload(Product.store),
        joinedload(Product.category),
        joinedload(Product.images)
    ).filter(
        Product.is_active == True
    )

    stores = []

    if payload["userrole"] == "Business Owner":

        stores = db.query(Store).filter(
            Store.user_id_fk == payload["userid"]
        ).all()

        store_ids = [store.id for store in stores]

        query = query.filter(
            Product.store_id_fk.in_(store_ids)
        )

    total = query.count()

    products = query.order_by(
        Product.create_date.desc()
    ).offset(skip).limit(limit).all()

    return {
        "page_type": "all_stores",
        "userrole": payload["userrole"],
        "current_user_id": payload["userid"],
        "stores": [
            serialize_store(store)
            for store in stores
        ],
        "total_products": total,
        "skip": skip,
        "limit": limit,
        "products": [
            serialize_product(product)
            for product in products
        ]
    }



@router.get("/api/{storename}")
def get_individual_store(
    storename: str,
    db: db_dependency,
    payload: user_dependency
):

    store = db.query(Store).filter(
        Store.storename == storename
    ).first()

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )

    products = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.images)
    ).filter(
        Product.store_id_fk == store.id,
        Product.is_active == True
    ).order_by(
        Product.create_date.desc()
    ).all()

    stores = []

    if payload["userrole"] == "Business Owner":

        stores = db.query(Store).filter(
            Store.user_id_fk == payload["userid"]
        ).all()

    return {
        "page_type": "single_store",
        "userrole": payload["userrole"],
        "current_user_id": payload["userid"],
        "store": serialize_store(store),
        "stores": [
            serialize_store(s)
            for s in stores
        ],
        "total_products": len(products),
        "products": [
            serialize_product(product)
            for product in products
        ]
    }


#---------------WEB PAGEs START----------------------------
@router.get('/create-store-page')
def render_create_store_page(request: Request):
    return templates.TemplateResponse(request=request, name="create_store.html")


@router.get("/", response_class=HTMLResponse)
def render_store_page(
    request: Request,
    payload: dict = Depends(require_login_redirect)
):
    print(payload)
    if isinstance(payload, RedirectResponse):
        return payload

    return templates.TemplateResponse(
        request=request,
        name="store.html"
    )


@router.get("/{storename}", response_class=HTMLResponse)
def render_individual_store_page(
    request: Request,
    storename: str,
    payload: dict = Depends(require_login_redirect)
):

    if isinstance(payload, RedirectResponse):
        return payload

    return templates.TemplateResponse(
        request=request,
        name="store.html"
    )
#---------------WEB PAGEs END  ----------------------------
'''
# ---------------- STORE HOME PAGE ----------------

@router.get("/")
def store_home_page(
    request: Request,
    db: db_dependency,
    # payload: user_dependency,
    payload: dict = Depends(require_login_redirect),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100)
):
    if isinstance(payload, RedirectResponse):
        return payload
    
    query = db.query(Product).options(
        joinedload(Product.store),
        joinedload(Product.category),
        joinedload(Product.images)
    ).filter(Product.is_active == True)

    total_products = query.count()

    products = (
        query.order_by(Product.create_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="store.html",
        context={
            "userrole": payload["userrole"],
            "products": products,
            "store": None,
            "total_products": total_products,
            "page_type": "all_stores",
            "skip": skip,
            "limit": limit
        }
    )


# ---------------- INDIVIDUAL STORE PAGE ----------------

@router.get("/{storename}")
def individual_store_page(
    request: Request,
    storename: str,
    db: db_dependency,
    # payload: user_dependency
    payload: dict = Depends(require_login_redirect)
):
    if isinstance(payload, RedirectResponse):
        return payload
     
    store = db.query(Store).filter(
        Store.storename == storename
    ).first()

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )

    products = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.images)
    ).filter(
        Product.store_id_fk == store.id,
        Product.is_active == True
    ).order_by(
        Product.create_date.desc()
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="store.html",
        context={
            "userrole": payload["userrole"],
            "store": store,
            "products": products,
            "total_products": len(products),
            "page_type": "single_store"
        }
    )
'''


'''

@router.get("/")
def store_details(db: db_dependency, payload: user_dependency,
                skip: int = Query(default=0, ge=0),
                limit: int = Query(default=20, ge=1, le=100)):
    
    products = db.query(Product).filter(Product.is_active == True).order_by(Product.create_date.desc()).offset(skip).limit(limit).all()


    return {
        "userrole": payload["userrole"],

        "total_products": len(products),

        "products": [
            {
                "id": product.id,
                "product_name": product.product_name,
                "mrp": product.mrp,
                "product_price": product.product_price,
                "product_description": product.product_description,
                "stock_quantity": product.stock_quantity,
                "main_img_url": product.main_img_url,
                "product_rating": product.product_rating,
                "rating_count": product.rating_count,
                "review_count": product.review_count,
                "is_active": product.is_active,
                "create_date": product.create_date,
                "update_date": product.update_date,
                "is_returnable": product.is_returnable,
                "slug": product.slug,
                "sku": product.sku,
                "weight": product.weight,
                "warrenty_period": product.warrenty_period,
                "discount_percentage": product.discount_percentage,
                "brand": product.brand,
                "user_id_fk": product.user_id_fk,
                "store_id_fk": product.store_id_fk,
                "category_id_fk": product.category_id_fk,

                # Relationship data
                "images": [
                    {
                        "id": image.id,
                        "product_id_fk": image.product_id_fk,
                        "image_url": image.image_url,
                        "is_primary": image.is_primary,
                        "display_order": image.display_order
                    }
                    for image in product.images
                ],

                "category": (
                    {
                        "id": product.category.id,
                        "category_name": product.category.category_name,
                        "description": product.category.description,
                        "parent_category_id_fk": product.category.parent_category_id_fk,
                        "is_active": product.category.is_active
                    }
                    if product.category else None
                )
            }
            for product in products
        ]
    }
    



@router.get("/{storename}")
def store_details(db: db_dependency, payload: user_dependency,
                storename: str = Path(min_length=1)):
    print(storename)
    store = get_owned_store(db, storename, payload)
    products = db.query(Product).filter(
        Product.store_id_fk == store.id,
        Product.is_active == True
    ).all()


    return {
        "userrole": payload["userrole"],

        "store": {
            "id": store.id,
            "storename": store.storename,
            "store_description": store.store_description,
            "store_dp_path": store.store_dp_path,
            "store_background_img_path": store.store_background_img_path,
            "create_date": store.create_date,
            "update_date": store.update_date,
            "user_id_fk": store.user_id_fk
        },

        "total_products": len(products),

        "products": [
            {
                "id": product.id,
                "product_name": product.product_name,
                "mrp": product.mrp,
                "product_price": product.product_price,
                "product_description": product.product_description,
                "stock_quantity": product.stock_quantity,
                "main_img_url": product.main_img_url,
                "product_rating": product.product_rating,
                "rating_count": product.rating_count,
                "review_count": product.review_count,
                "is_active": product.is_active,
                "create_date": product.create_date,
                "update_date": product.update_date,
                "is_returnable": product.is_returnable,
                "slug": product.slug,
                "sku": product.sku,
                "weight": product.weight,
                "warrenty_period": product.warrenty_period,
                "discount_percentage": product.discount_percentage,
                "brand": product.brand,
                "user_id_fk": product.user_id_fk,
                "store_id_fk": product.store_id_fk,
                "category_id_fk": product.category_id_fk,

                # Relationship data
                "images": [
                    {
                        "id": image.id,
                        "product_id_fk": image.product_id_fk,
                        "image_url": image.image_url,
                        "is_primary": image.is_primary,
                        "display_order": image.display_order
                    }
                    for image in product.images
                ],

                "category": (
                    {
                        "id": product.category.id,
                        "category_name": product.category.category_name,
                        "description": product.category.description,
                        "parent_category_id_fk": product.category.parent_category_id_fk,
                        "is_active": product.category.is_active
                    }
                    if product.category else None
                )
            }
            for product in products
        ]
    }
    
    

'''