from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timedelta
from app.database import get_products_collection, get_orders_collection
from app.models import User
from app.schemas import SalesAnalytics, InventoryAnalytics, ReportResponse
from app.auth import get_current_active_user

router = APIRouter(prefix="/reports", tags=["reports"])

def check_permission(user: User, permission: str):
    if user.role == "admin":
        return True
    if user.role == "manager" and permission in ["view_reports", "view_analytics"]:
        return True
    return permission in user.permissions

@router.get("/sales", response_model=SalesAnalytics)
async def get_sales_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_active_user)
):
    if not check_permission(current_user, "view_reports"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    orders_collection = get_orders_collection()
    
    # Get orders from last N days
    start_date = datetime.utcnow() - timedelta(days=days)
    orders = list(orders_collection.find({
        "created_at": {"$gte": start_date},
        "status": {"$ne": "cancelled"}
    }))
    
    total_sales = sum(order["total_amount"] for order in orders)
    total_orders = len(orders)
    
    # Top products
    product_sales = {}
    for order in orders:
        for item in order["items"]:
            product_name = item["product_name"]
            if product_name in product_sales:
                product_sales[product_name] += item["total"]
            else:
                product_sales[product_name] = item["total"]
    
    top_products = [
        {"name": name, "sales": sales}
        for name, sales in sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    # Sales by month (simplified)
    sales_by_month = [
        {"month": "Current Month", "sales": total_sales}
    ]
    
    return SalesAnalytics(
        total_sales=total_sales,
        total_orders=total_orders,
        top_products=top_products,
        sales_by_month=sales_by_month
    )

@router.get("/inventory", response_model=InventoryAnalytics)
async def get_inventory_analytics(
    current_user: User = Depends(get_current_active_user)
):
    if not check_permission(current_user, "view_reports"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    products_collection = get_products_collection()
    products = list(products_collection.find())
    
    total_products = len(products)
    low_stock_products = []
    out_of_stock_products = []
    total_inventory_value = 0
    
    for product in products:
        total_inventory_value += product["price"] * product["stock_quantity"]
        
        if product["stock_quantity"] == 0:
            out_of_stock_products.append({
                "name": product["name"],
                "sku": product["sku"]
            })
        elif product["stock_quantity"] <= product.get("low_stock_threshold", 10):
            low_stock_products.append({
                "name": product["name"],
                "sku": product["sku"],
                "current_stock": product["stock_quantity"],
                "threshold": product.get("low_stock_threshold", 10)
            })
    
    return InventoryAnalytics(
        total_products=total_products,
        low_stock_products=low_stock_products,
        out_of_stock_products=out_of_stock_products,
        total_inventory_value=total_inventory_value
    )

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user)
):
    if not check_permission(current_user, "view_reports"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    products_collection = get_products_collection()
    orders_collection = get_orders_collection()
    
    # Get basic stats
    total_products = products_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    pending_orders = orders_collection.count_documents({"status": "pending"})
    
    # Recent orders
    recent_orders = list(orders_collection.find().sort("created_at", -1).limit(5))
    for order in recent_orders:
        order["_id"] = str(order["_id"])
    
    # Low stock alerts
    low_stock_products = list(products_collection.find({
        "$expr": {"$lte": ["$stock_quantity", "$low_stock_threshold"]}
    }).limit(5))
    
    for product in low_stock_products:
        product["_id"] = str(product["_id"])
    
    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "recent_orders": recent_orders,
        "low_stock_alerts": low_stock_products
    }