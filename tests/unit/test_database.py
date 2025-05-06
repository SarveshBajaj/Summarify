import pytest
import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the database module
from app.database import (
    get_db_connection, init_db, create_user, get_user, 
    verify_password, authenticate_user, log_query, 
    get_user_queries, get_query_stats
)

# Test database setup and teardown
@pytest.fixture
def test_db():
    """Create a temporary test database"""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Patch the DB_PATH to use our temporary database
    with patch('app.database.DB_PATH', db_path):
        # Initialize the database
        init_db()
        
        # Yield the database path for tests to use
        yield db_path
        
    # Clean up after tests
    os.close(db_fd)
    os.unlink(db_path)

def test_init_db(test_db):
    """Test database initialization"""
    # Connect to the test database
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Check if tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Verify tables exist
    assert 'users' in tables
    assert 'queries' in tables
    
    # Check users table structure
    cursor.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cursor.fetchall()}
    assert 'id' in columns
    assert 'username' in columns
    assert 'email' in columns
    assert 'hashed_password' in columns
    assert 'disabled' in columns
    assert 'created_at' in columns
    assert 'last_login' in columns
    
    # Check queries table structure
    cursor.execute("PRAGMA table_info(queries)")
    columns = {row[1] for row in cursor.fetchall()}
    assert 'id' in columns
    assert 'user_id' in columns
    assert 'url' in columns
    assert 'provider_type' in columns
    assert 'summary_length' in columns
    assert 'valid' in columns
    assert 'processing_time' in columns
    assert 'created_at' in columns
    
    conn.close()

def test_create_and_get_user(test_db):
    """Test creating and retrieving a user"""
    # Create a test user
    username = "testuser"
    password = "testpassword"
    email = "test@example.com"
    
    # Create the user
    user = create_user(username, password, email)
    
    # Verify user was created
    assert user is not None
    assert user["username"] == username
    assert user["email"] == email
    assert "id" in user
    
    # Retrieve the user
    retrieved_user = get_user(username)
    
    # Verify retrieved user matches created user
    assert retrieved_user is not None
    assert retrieved_user["username"] == username
    assert retrieved_user["email"] == email
    assert retrieved_user["id"] == user["id"]
    assert "hashed_password" in retrieved_user
    
    # Verify password was hashed (not stored in plaintext)
    assert retrieved_user["hashed_password"] != password
    
    # Verify password verification works
    assert verify_password(password, retrieved_user["hashed_password"])
    assert not verify_password("wrongpassword", retrieved_user["hashed_password"])

def test_authenticate_user(test_db):
    """Test user authentication"""
    # Create a test user
    username = "authuser"
    password = "authpassword"
    create_user(username, password)
    
    # Test successful authentication
    user = authenticate_user(username, password)
    assert user is not None
    assert user["username"] == username
    
    # Test failed authentication with wrong password
    user = authenticate_user(username, "wrongpassword")
    assert user is None
    
    # Test failed authentication with non-existent user
    user = authenticate_user("nonexistentuser", password)
    assert user is None

def test_log_and_get_query(test_db):
    """Test logging and retrieving queries"""
    # Create a test user
    user = create_user("queryuser", "querypassword")
    user_id = user["id"]
    
    # Log a query
    url = "https://www.youtube.com/watch?v=testid"
    provider_type = "youtube"
    summary_length = 500
    valid = True
    processing_time = 5.2
    
    query_id = log_query(
        user_id=user_id,
        url=url,
        provider_type=provider_type,
        summary_length=summary_length,
        valid=valid,
        processing_time=processing_time
    )
    
    # Verify query was logged
    assert query_id > 0
    
    # Get user queries
    queries = get_user_queries(user_id)
    
    # Verify query was retrieved
    assert len(queries) == 1
    query = queries[0]
    assert query["id"] == query_id
    assert query["user_id"] == user_id
    assert query["url"] == url
    assert query["provider_type"] == provider_type
    assert query["summary_length"] == summary_length
    assert query["valid"] == valid
    assert abs(query["processing_time"] - processing_time) < 0.001  # Float comparison
    assert "created_at" in query

def test_get_query_stats(test_db):
    """Test query statistics"""
    # Create a test user
    user = create_user("statsuser", "statspassword")
    user_id = user["id"]
    
    # Log multiple queries with different properties
    log_query(user_id, "https://youtube.com/1", "youtube", 500, True, 5.0)
    log_query(user_id, "https://youtube.com/2", "youtube", 600, False, 6.0)
    log_query(user_id, "https://example.com", "web", 700, True, 7.0)
    
    # Get query stats
    stats = get_query_stats()
    
    # Verify stats
    assert stats["total_queries"] == 3
    assert stats["by_provider"]["youtube"] == 2
    assert stats["by_provider"]["web"] == 1
    
    # SQLite might return booleans as integers (1 for True, 0 for False)
    # or strings depending on the implementation
    true_key = "1" if "1" in stats["valid_summaries"] else "True"
    false_key = "0" if "0" in stats["valid_summaries"] else "False"
    
    assert stats["valid_summaries"][true_key] == 2
    assert stats["valid_summaries"][false_key] == 1
    assert 5.0 <= stats["avg_processing_time"] <= 7.0  # Should be around 6.0

def test_duplicate_username(test_db):
    """Test handling of duplicate usernames"""
    # Create a user
    username = "duplicateuser"
    create_user(username, "password1")
    
    # Try to create another user with the same username
    duplicate_user = create_user(username, "password2")
    
    # Should return None for duplicate username
    assert duplicate_user is None

def test_user_queries_limit(test_db):
    """Test query limit parameter"""
    # Create a test user
    user = create_user("limituser", "limitpassword")
    user_id = user["id"]
    
    # Log multiple queries
    for i in range(15):
        log_query(user_id, f"https://example.com/{i}", "web", 500, True, 5.0)
    
    # Get queries with default limit (10)
    queries = get_user_queries(user_id)
    assert len(queries) == 10
    
    # Get queries with custom limit
    queries = get_user_queries(user_id, limit=5)
    assert len(queries) == 5
    
    # Get all queries
    queries = get_user_queries(user_id, limit=20)
    assert len(queries) == 15
