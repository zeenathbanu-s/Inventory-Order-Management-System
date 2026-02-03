from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from typing import List
from bson import ObjectId
from datetime import datetime
import os
import uuid
from app.database import get_products_collection
from app.models import Product, User
from app.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.auth import get_current_active_user

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_active_user)
):
    try:
        products_collection = get_products_collection()
        
        # Check if SKU already exists
        if products_collection.find_one({"sku": product.sku}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this SKU already exists"
            )
        
        product_data = product.dict()
        product_data["created_at"] = datetime.utcnow()
        product_data["updated_at"] = datetime.utcnow()
        
        result = products_collection.insert_one(product_data)
        created_product = products_collection.find_one({"_id": result.inserted_id})
        
        # Ensure all fields are properly formatted
        response_data = {
            "id": str(created_product["_id"]),
            "name": created_product["name"],
            "description": created_product.get("description"),
            "price": float(created_product["price"]),
            "stock_quantity": int(created_product["stock_quantity"]),
            "category": created_product.get("category"),
            "sku": created_product["sku"],
            "image_url": created_product.get("image_url"),
            "low_stock_threshold": int(created_product.get("low_stock_threshold", 10)),
            "created_at": created_product["created_at"],
            "updated_at": created_product["updated_at"]
        }
        
        return ProductResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    try:
        products_collection = get_products_collection()
        products = list(products_collection.find().skip(skip).limit(limit))
        
        result = []
        for product in products:
            try:
                # Ensure all required fields exist with defaults
                product_data = {
                    "id": str(product["_id"]),
                    "name": product.get("name", ""),
                    "description": product.get("description"),
                    "price": float(product.get("price", 0)),
                    "stock_quantity": int(product.get("stock_quantity", 0)),
                    "category": product.get("category"),
                    "sku": product.get("sku", ""),
                    "image_url": product.get("image_url"),
                    "low_stock_threshold": int(product.get("low_stock_threshold", 10)),
                    "created_at": product.get("created_at", datetime.utcnow()),
                    "updated_at": product.get("updated_at", datetime.utcnow())
                }
                result.append(ProductResponse(**product_data))
            except Exception as e:
                print(f"Error processing product {product.get('_id')}: {e}")
                continue
        
        return result
    except Exception as e:
        print(f"Error in get_products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve products: {str(e)}"
        )

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    products_collection = get_products_collection()
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse(
        id=str(product["_id"]),
        **{k: v for k, v in product.items() if k != "_id"}
    )

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    products_collection = get_products_collection()
    
    # Check if product exists
    existing_product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Prepare update data
    update_data = {k: v for k, v in product_update.dict().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        products_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
    
    updated_product = products_collection.find_one({"_id": ObjectId(product_id)})
    
    return ProductResponse(
        id=str(updated_product["_id"]),
        **{k: v for k, v in updated_product.items() if k != "_id"}
    )

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    products_collection = get_products_collection()
    result = products_collection.delete_one({"_id": ObjectId(product_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {"message": "Product deleted successfully"}

@router.post("/upload-image/{product_id}")
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    # Check if product exists
    products_collection = get_products_collection()
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads/products"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update product with image URL
        image_url = f"/static/uploads/products/{unique_filename}"
        products_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"image_url": image_url, "updated_at": datetime.utcnow()}}
        )
        
        return {"message": "Image uploaded successfully", "image_url": image_url}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )