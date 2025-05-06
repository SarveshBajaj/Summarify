from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
import os
from .schemas import UserCreate, User, TokenData

# In production, use environment variables for these
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# In-memory user database - in production, use a real database
fake_users_db: Dict[str, Dict[str, Any]] = {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)

def get_user(db: Dict[str, Dict[str, Any]], username: str) -> Optional[Dict[str, Any]]:
    """Get a user from the database"""
    if username in db:
        user_dict = db[username]
        return user_dict
    return None

def authenticate_user(db: Dict[str, Dict[str, Any]], username: str, password: str) -> Union[Dict[str, Any], bool]:
    """Authenticate a user"""
    user = get_user(db, username)
    if not user:
        logger.warning(f"User not found: {username}")
        return False
    if not verify_password(password, user["hashed_password"]):
        logger.warning(f"Invalid password for user: {username}")
        return False
    logger.info(f"User authenticated: {username}")
    return user

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

    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        logger.warning(f"User from token not found: {token_data.username}")
        raise credentials_exception

    logger.debug(f"Authenticated request from user: {token_data.username}")
    return token_data.username

async def get_current_active_user(current_user: str = Depends(get_current_user)) -> str:
    """Get the current active user"""
    user = get_user(fake_users_db, username=current_user)
    if user.get("disabled", False):
        logger.warning(f"Disabled user attempted access: {current_user}")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def register_user(user: UserCreate) -> Dict[str, Any]:
    """Register a new user"""
    if user.username in fake_users_db:
        logger.warning(f"Registration failed: {user.username} already exists")
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)
    user_data = {
        "username": user.username,
        "hashed_password": hashed_password,
        "email": user.email,
        "disabled": False
    }

    fake_users_db[user.username] = user_data
    logger.info(f"User registered: {user.username}")
    return user_data
