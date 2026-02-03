from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.database import get_users_collection
from app.models import User
from app.schemas import UserCreate
from app.auth import get_current_active_user, get_password_hash

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create users")
    
    users_collection = get_users_collection()
    
    # Check if username exists
    if users_collection.find_one({"username": user_data.username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Set permissions based on role
    permissions = []
    if user_data.role == "manager":
        permissions = ["create_product", "edit_product", "view_reports", "manage_orders"]
    elif user_data.role == "staff":
        permissions = ["view_products", "create_order", "view_orders"]
    
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        permissions=permissions,
        is_active=True
    )
    
    user_dict = new_user.dict(by_alias=True, exclude_none=True)
    if "_id" in user_dict and user_dict["_id"] is None:
        del user_dict["_id"]
    
    result = users_collection.insert_one(user_dict)
    created_user = users_collection.find_one({"_id": result.inserted_id})
    created_user["_id"] = str(created_user["_id"])
    
    # Remove password from response
    del created_user["hashed_password"]
    
    return created_user

@router.get("/")
async def get_users(
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    users_collection = get_users_collection()
    users = list(users_collection.find({}, {"hashed_password": 0}))
    
    for user in users:
        user["_id"] = str(user["_id"])
    
    return users

@router.put("/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update user roles")
    
    if role not in ["admin", "manager", "staff"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    users_collection = get_users_collection()
    
    # Set permissions based on role
    permissions = []
    if role == "manager":
        permissions = ["create_product", "edit_product", "view_reports", "manage_orders"]
    elif role == "staff":
        permissions = ["view_products", "create_order", "view_orders"]
    elif role == "admin":
        permissions = ["all"]
    
    from bson import ObjectId
    try:
        object_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = users_collection.update_one(
        {"_id": object_id},
        {"$set": {"role": role, "permissions": permissions}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User role updated successfully"}