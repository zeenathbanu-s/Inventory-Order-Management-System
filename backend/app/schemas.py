from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int
    category: Optional[str] = None
    sku: str
    low_stock_threshold: int = 10
    image_url: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    category: Optional[str] = None
    low_stock_threshold: Optional[int] = None
    image_url: Optional[str] = None

class ProductResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int
    category: Optional[str] = None
    sku: str
    image_url: Optional[str] = None
    low_stock_threshold: int
    created_at: datetime
    updated_at: datetime

class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str  # Changed from EmailStr to str
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: float
    total: float

class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_name: str
    customer_email: str
    items: List[OrderItemResponse]
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime

class OrderStatusUpdate(BaseModel):
    status: str

class ReportResponse(BaseModel):
    id: str
    report_type: str
    data: dict
    generated_by: str
    generated_at: datetime

class SalesAnalytics(BaseModel):
    total_sales: float
    total_orders: int
    top_products: List[dict]
    sales_by_month: List[dict]

class InventoryAnalytics(BaseModel):
    total_products: int
    low_stock_products: List[dict]
    out_of_stock_products: List[dict]
    total_inventory_value: float

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "staff"
    permissions: List[str] = []