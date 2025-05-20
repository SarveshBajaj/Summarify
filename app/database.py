import sqlite3
import os
from loguru import logger
from passlib.context import CryptContext
from typing import Optional, Dict, List, Any, Tuple
import json
from datetime import datetime

# Import encryption utilities
from .encryption import SECRET_KEY

# Password hashing context with enhanced security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to hash password with additional salt from our secret key
def hash_password(password: str) -> str:
    """Hash password with additional salt from our secret key"""
    # Add first 8 bytes of SECRET_KEY as additional salt
    salted_password = password + SECRET_KEY[:8].decode()
    return pwd_context.hash(salted_password)

# Function to verify password with additional salt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with additional salt from our secret key"""
    # Add first 8 bytes of SECRET_KEY as additional salt
    salted_password = plain_password + SECRET_KEY[:8].decode()
    return pwd_context.verify(salted_password, hashed_password)

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "summarify.db")

# Ensure data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    """Initialize the database with required tables"""
    logger.info(f"Initializing database at {DB_PATH}")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        hashed_password TEXT NOT NULL,
        disabled BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')

    # Create queries table to track user summarization requests
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        url TEXT NOT NULL,
        provider_type TEXT NOT NULL,
        model_type TEXT DEFAULT 'huggingface',
        model_name TEXT,
        summary_length INTEGER,
        valid BOOLEAN,
        processing_time REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()

    logger.info("Database initialized successfully")

# User management functions
def create_user(username: str, password: str, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Create a new user with hashed password"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Hash the password with our enhanced security
        hashed_password = hash_password(password)

        cursor.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"User created: {username} (ID: {user_id})")

        return {
            "id": user_id,
            "username": username,
            "email": email,
            "disabled": False
        }
    except sqlite3.IntegrityError:
        logger.warning(f"Failed to create user: {username} (already exists)")
        return None
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return None

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        conn.close()

        if user:
            return dict(user)
        return None
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return None

# verify_password function is now defined at the top of the file

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user and update last login time"""
    user = get_user(username)

    if not user:
        logger.warning(f"Authentication failed: User not found - {username}")
        return None

    if not verify_password(password, user["hashed_password"]):
        logger.warning(f"Authentication failed: Invalid password - {username}")
        return None

    # Update last login time
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user["id"],)
        )

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating last login: {str(e)}")

    logger.info(f"User authenticated: {username}")
    return user

# Import encryption utilities
from .encryption import encrypt_text, decrypt_text

# User API key management functions
def set_user_api_key(user_id: int, provider: str, api_key: str) -> bool:
    """Set or update API key for a specific user and provider"""
    try:
        # Encrypt the API key before storing it
        encrypted_key = encrypt_text(api_key)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if key already exists
        cursor.execute(
            "SELECT id FROM user_api_keys WHERE user_id = ? AND provider = ?",
            (user_id, provider)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing key
            cursor.execute(
                "UPDATE user_api_keys SET api_key = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND provider = ?",
                (encrypted_key, user_id, provider)
            )
        else:
            # Insert new key
            cursor.execute(
                "INSERT INTO user_api_keys (user_id, provider, api_key) VALUES (?, ?, ?)",
                (user_id, provider, encrypted_key)
            )

        conn.commit()
        conn.close()

        logger.info(f"Encrypted API key for {provider} set for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error setting user API key: {str(e)}")
        return False

def get_user_api_key(user_id: int, provider: str) -> Optional[str]:
    """Get API key for a specific user and provider"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT api_key FROM user_api_keys WHERE user_id = ? AND provider = ?",
            (user_id, provider)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            # Decrypt the API key before returning it
            encrypted_key = result[0]
            return decrypt_text(encrypted_key)
        return None
    except Exception as e:
        logger.error(f"Error getting user API key: {str(e)}")
        return None

def get_user_api_keys(user_id: int) -> Dict[str, str]:
    """Get all API keys for a specific user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT provider, api_key FROM user_api_keys WHERE user_id = ?",
            (user_id,)
        )
        results = cursor.fetchall()
        conn.close()

        # Decrypt all API keys before returning them
        return {provider: decrypt_text(api_key) for provider, api_key in results}
    except Exception as e:
        logger.error(f"Error getting user API keys: {str(e)}")
        return {}

# Query tracking functions
def log_query(
    user_id: int,
    url: str,
    provider_type: str,
    summary_length: int,
    valid: bool,
    processing_time: float,
    model_type: str = "huggingface",
    model_name: Optional[str] = None
) -> int:
    """Log a summarization query"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO queries
            (user_id, url, provider_type, model_type, model_name, summary_length, valid, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, url, provider_type, model_type, model_name, summary_length, valid, processing_time)
        )

        query_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Query logged: ID {query_id} for user {user_id}")
        return query_id
    except Exception as e:
        logger.error(f"Error logging query: {str(e)}")
        return -1

def get_user_queries(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent queries for a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM queries
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )

        queries = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return queries
    except Exception as e:
        logger.error(f"Error getting user queries: {str(e)}")
        return []

def get_query_stats() -> Dict[str, Any]:
    """Get overall query statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total queries
        cursor.execute("SELECT COUNT(*) as count FROM queries")
        total_count = cursor.fetchone()["count"]

        # Queries by provider type
        cursor.execute(
            """
            SELECT provider_type, COUNT(*) as count
            FROM queries
            GROUP BY provider_type
            """
        )
        provider_counts = {row["provider_type"]: row["count"] for row in cursor.fetchall()}

        # Valid vs invalid summaries
        cursor.execute(
            """
            SELECT valid, COUNT(*) as count
            FROM queries
            GROUP BY valid
            """
        )
        valid_counts = {str(row["valid"]): row["count"] for row in cursor.fetchall()}

        # Average processing time
        cursor.execute("SELECT AVG(processing_time) as avg_time FROM queries")
        avg_time = cursor.fetchone()["avg_time"]

        conn.close()

        return {
            "total_queries": total_count,
            "by_provider": provider_counts,
            "valid_summaries": valid_counts,
            "avg_processing_time": avg_time
        }
    except Exception as e:
        logger.error(f"Error getting query stats: {str(e)}")
        return {
            "total_queries": 0,
            "by_provider": {},
            "valid_summaries": {},
            "avg_processing_time": 0
        }

# Initialize the database when the module is imported
init_db()
