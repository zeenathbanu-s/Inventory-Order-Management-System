from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_users_collection
from app.models import User
from app.schemas import TokenData
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return get_password_hash(plain_password) == hashed_password

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(username: str):
    users_collection = get_users_collection()
    user_data = users_collection.find_one({"username": username})
    if user_data:
        # Convert ObjectId to string for Pydantic
        if "_id" in user_data:
            user_data["_id"] = str(user_data["_id"])
        return User(**user_data)
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def create_admin_user():
    """Create default admin user if not exists"""
    users_collection = get_users_collection()
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    if not users_collection.find_one({"username": admin_username}):
        admin_user = User(
            username=admin_username,
            hashed_password=get_password_hash(admin_password),
            role="admin",
            is_active=True
        )
        # Convert to dict and remove None id for insertion
        user_dict = admin_user.dict(by_alias=True, exclude_none=True)
        if "_id" in user_dict and user_dict["_id"] is None:
            del user_dict["_id"]
        users_collection.insert_one(user_dict)