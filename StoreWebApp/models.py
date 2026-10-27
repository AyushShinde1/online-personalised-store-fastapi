from sqlalchemy import (Column, String, Integer, Boolean,
                        Float, DateTime, ForeignKey, Numeric, Text,
                        UniqueConstraint, CheckConstraint)
from sqlalchemy.orm import relationship

from datetime import datetime, timezone

from .database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Users(Base):
    __tablename__ = 'users'

    id=Column(Integer, primary_key=True, index=True)
    username=Column(String(100), unique=True, nullable=False, index=True)
    #password=Column(String, nullable=False) #storing it temporarily for testing
    first_name=Column(String(100), nullable=False)
    last_name=Column(String(100))
    hashed_password=Column(String, nullable=False)
    role=Column(String(30), nullable=False, default="user")
    is_active=Column(Boolean,nullable=False, default=True)
    phone_number=Column(String(20),nullable=False)
    email=Column(String(225), unique=True, index=True)

    stores = relationship("Store", back_populates="owner")
    reviews = relationship("ProductRatingReview", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")


class Store(Base):
    __tablename__ = 'stores'

    id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String(200), nullable=False)
    create_date = Column(DateTime(timezone=True), nullable=False)
    update_date = Column(DateTime(timezone=True),nullable=False, onupdate=utc_now)
    user_id_fk = Column(Integer, ForeignKey("users.id"))

    owner = relationship("Users", back_populates="stores")
    products = relationship("Product", back_populates="store")


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(200), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    product_price = Column(Numeric(10, 2), nullable=False)
    product_description = Column(Text, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    main_img_url = Column(String(2048))
    product_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, nullable=False, default=0)
    review_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    create_date = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    update_date = Column(DateTime(timezone=True), onupdate=utc_now)
    is_returnable = Column(Boolean, default=False)
    slug = Column(String) #URL-friendly product identifier
    sku = Column(String(100), unique=True, nullable=False) #Unique product/stock identifier
    weight = Column(Numeric(10, 3))
    warrenty_period = Column(String(100))
    discount_percentage = Column(Integer)
    brand = Column(String(100))
    user_id_fk = Column(Integer, ForeignKey("users.id"))
    store_id_fk = Column(Integer, ForeignKey("stores.id"))
    category_id_fk = Column(Integer, ForeignKey("categories.id"))
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")
    reviews = relationship("ProductRatingReview", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")


class ProductRatingReview(Base):
    __tablename__ = 'productRatingReview'
    __table_args__ = (
        UniqueConstraint("user_id_fk","product_id_fk",name="uq_user_product_review"),
    )

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Float)
    review = Column(String)
    product_id_fk = Column(Integer, ForeignKey("products.id"))
    user_id_fk = Column(Integer, ForeignKey("users.id"), nullable=False) #identifies who submitted the review
    user = relationship("Users", back_populates="reviews")
    product = relationship("Product",back_populates="reviews")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    parent_category_id_fk = Column(Integer,ForeignKey("categories.id"),nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    products = relationship("Product", back_populates="category")
    parent = relationship("Category",remote_side="Category.id",back_populates="children")
    children = relationship("Category", back_populates="parent")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id_fk = Column(Integer,ForeignKey("products.id", ondelete="CASCADE"),nullable=False,index=True)
    image_url = Column(String(2048), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)
    product = relationship("Product", back_populates="images")


class CartItem(Base):
    __tablename__ = "cart_items"

    __table_args__ = (
        UniqueConstraint("user_id_fk", "product_id_fk", name="uq_cart_user_product"),
        CheckConstraint("quantity > 0", name="ck_cart_quantity_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    user_id_fk = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id_fk = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    create_date = Column(DateTime(timezone=True),nullable=False,default=utc_now)
    update_date = Column(DateTime(timezone=True), onupdate=utc_now)

    user = relationship("Users", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")