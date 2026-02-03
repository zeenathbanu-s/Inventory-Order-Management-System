from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from datetime import datetime
import uuid
from app.database import get_orders_collection, get_products_collection
from app.models import User, Order, OrderItem
from app.schemas import OrderCreate, OrderResponse, OrderStatusUpdate
from app.auth import get_current_active_user
from app.email_service import email_service

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_active_user)
):
    orders_collection = get_orders_collection()
    products_collection = get_products_collection()
    
    order_items = []
    total_amount = 0.0
    
    # Process each item in the order
    for item in order.items:
        if not ObjectId.is_valid(item.product_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid product ID: {item.product_id}"
            )
        
        product = products_collection.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product not found: {item.product_id}"
            )
        
        # Check stock availability
        if product["stock_quantity"] < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product['name']}. Available: {product['stock_quantity']}, Requested: {item.quantity}"
            )
        
        # Calculate item total
        item_total = product["price"] * item.quantity
        total_amount += item_total
        
        # Create order item
        order_item = OrderItem(
            product_id=str(product["_id"]),
            product_name=product["name"],
            quantity=item.quantity,
            price=product["price"],
            total=item_total
        )
        order_items.append(order_item)
        
        # Update product stock
        new_stock = product["stock_quantity"] - item.quantity
        products_collection.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$set": {"stock_quantity": new_stock, "updated_at": datetime.utcnow()}}
        )
    
    # Generate order number
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    # Create order
    order_data = {
        "order_number": order_number,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "items": [item.dict() for item in order_items],
        "total_amount": total_amount,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = orders_collection.insert_one(order_data)
    created_order = orders_collection.find_one({"_id": result.inserted_id})
    
    # Send order confirmation email
    try:
        await email_service.send_order_confirmation(
            order_number, 
            order.customer_email, 
            total_amount
        )
    except Exception as e:
        print(f"Failed to send order confirmation email: {e}")
    
    # Check for low stock alerts
    try:
        for item in order_items:
            product = products_collection.find_one({"_id": ObjectId(item.product_id)})
            if product and product["stock_quantity"] <= product.get("low_stock_threshold", 10):
                # Send low stock alert to admin (you can get admin email from env or database)
                admin_email = "admin@inventory.com"  # Replace with actual admin email
                await email_service.send_low_stock_alert(
                    product["name"],
                    product["stock_quantity"],
                    admin_email
                )
    except Exception as e:
        print(f"Failed to send low stock alert: {e}")
    
    return OrderResponse(
        id=str(created_order["_id"]),
        **{k: v for k, v in created_order.items() if k != "_id"}
    )

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    current_user: User = Depends(get_current_active_user)
):
    orders_collection = get_orders_collection()
    
    query = {}
    if status:
        query["status"] = status
    
    orders = list(orders_collection.find(query).skip(skip).limit(limit).sort("created_at", -1))
    
    return [
        OrderResponse(
            id=str(order["_id"]),
            **{k: v for k, v in order.items() if k != "_id"}
        )
        for order in orders
    ]

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID"
        )
    
    orders_collection = get_orders_collection()
    order = orders_collection.find_one({"_id": ObjectId(order_id)})
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse(
        id=str(order["_id"]),
        **{k: v for k, v in order.items() if k != "_id"}
    )

@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID"
        )
    
    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    orders_collection = get_orders_collection()
    
    # Check if order exists
    existing_order = orders_collection.find_one({"_id": ObjectId(order_id)})
    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update order status
    orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": status_update.status, "updated_at": datetime.utcnow()}}
    )
    
    updated_order = orders_collection.find_one({"_id": ObjectId(order_id)})
    
    return OrderResponse(
        id=str(updated_order["_id"]),
        **{k: v for k, v in updated_order.items() if k != "_id"}
    )

@router.delete("/{order_id}")
async def delete_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID"
        )
    
    orders_collection = get_orders_collection()
    products_collection = get_products_collection()
    
    # Get order details before deletion
    order = orders_collection.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Restore stock quantities if order is being cancelled
    if order["status"] in ["pending", "confirmed"]:
        for item in order["items"]:
            product = products_collection.find_one({"_id": ObjectId(item["product_id"])})
            if product:
                new_stock = product["stock_quantity"] + item["quantity"]
                products_collection.update_one(
                    {"_id": ObjectId(item["product_id"])},
                    {"$set": {"stock_quantity": new_stock, "updated_at": datetime.utcnow()}}
                )
    
    # Delete the order
    result = orders_collection.delete_one({"_id": ObjectId(order_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return {"message": "Order deleted successfully"}