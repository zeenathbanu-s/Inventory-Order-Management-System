from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    username: str
    hashed_password: str
    role: str = "staff"  # admin, manager, staff
    is_active: bool = True
    permissions: List[str] = []  # ["create_product", "edit_product", "delete_product", "view_reports"]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class Product(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int
    category: Optional[str] = None
    sku: str
    image_url: Optional[str] = None  # For product images
    low_stock_threshold: int = 10
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: float
    total: float

class Order(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    order_number: str
    customer_name: str
    customer_email: str
    items: List[OrderItem]
    total_amount: float
    status: str = "pending"  # pending, confirmed, shipped, delivered, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class Report(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    report_type: str  # "sales", "inventory", "low_stock"
    data: dict
    generated_by: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class Notification(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    type: str  # "low_stock", "order_placed", "order_shipped"
    message: str
    recipient_email: str
    sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True