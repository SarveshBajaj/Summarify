from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
import os
from .schemas import UserCreate, User, TokenData
from .database import authenticate_user as db_authenticate_user, create_user, get_user as db_get_user

# Import encryption utilities
from .encryption import SECRET_KEY as ENCRYPTION_KEY

# Use the encryption key for JWT as well
SECRET_KEY = os.environ.get("SECRET_KEY", ENCRYPTION_KEY.decode())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Created access token for user: {data.get('sub')}")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Get the current user from the JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token missing username")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.warning(f"JWT error: {str(e)}")
        raise credentials_exception

    user = db_get_user(username=token_data.username)
    if user is None:
        logger.warning(f"User from token not found: {token_data.username}")
        raise credentials_exception

    logger.debug(f"Authenticated request from user: {token_data.username}")
    return token_data.username

async def get_current_active_user(current_user: str = Depends(get_current_user)) -> str:
    """Get the current active user"""
    user = db_get_user(username=current_user)
    if user.get("disabled", False):
        logger.warning(f"Disabled user attempted access: {current_user}")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_user_id(current_user: str = Depends(get_current_user)) -> int:
    """Get the current user's ID"""
    user = db_get_user(username=current_user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user.get("id", 0)  # Default to 0 if id is not found

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user"""
    return db_authenticate_user(username, password)

def register_user(user: UserCreate) -> Dict[str, Any]:
    """Register a new user"""
    # Check if user already exists
    existing_user = db_get_user(user.username)
    if existing_user:
        logger.warning(f"Registration failed: {user.username} already exists")
        raise HTTPException(status_code=400, detail="Username already registered")

    # Create new user in database
    user_data = create_user(user.username, user.password, user.email)
    if not user_data:
        logger.error(f"Failed to create user: {user.username}")
        raise HTTPException(status_code=500, detail="Failed to create user")

    logger.info(f"User registered: {user.username}")
    return user_data
