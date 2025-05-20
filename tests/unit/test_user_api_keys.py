import pytest
from unittest.mock import patch, MagicMock

# Test data
TEST_USER_ID = 999
TEST_OPENAI_KEY = "test-openai-key"
TEST_CLAUDE_KEY = "test-claude-key"

@patch('app.database.get_db_connection')
def test_set_user_api_key(mock_get_db_connection):
    """Test setting a user API key"""
    # Import here to avoid circular imports during test collection
    from app.database import set_user_api_key

    # Mock the database connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db_connection.return_value = mock_conn

    # Call the function
    result = set_user_api_key(TEST_USER_ID, "openai", TEST_OPENAI_KEY)

    # Check the result
    assert result == True

    # Verify the database was called correctly
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called()
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()

@patch('app.database.get_db_connection')
def test_get_user_api_key(mock_get_db_connection):
    """Test getting a user API key"""
    # Import here to avoid circular imports during test collection
    from app.database import get_user_api_key

    # Mock the database connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db_connection.return_value = mock_conn

    # Mock the cursor.fetchone method to return a key
    mock_cursor.fetchone.return_value = (TEST_OPENAI_KEY,)

    # Call the function
    key = get_user_api_key(TEST_USER_ID, "openai")

    # Check the result
    assert key == TEST_OPENAI_KEY

    # Verify the database was called correctly
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    mock_conn.close.assert_called_once()

    # Test with no key found
    mock_conn.reset_mock()
    mock_cursor.reset_mock()
    mock_cursor.fetchone.return_value = None

    key = get_user_api_key(TEST_USER_ID, "nonexistent")
    assert key is None

@patch('app.database.get_db_connection')
def test_get_user_api_keys(mock_get_db_connection):
    """Test getting all user API keys"""
    # Import here to avoid circular imports during test collection
    from app.database import get_user_api_keys

    # Mock the database connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db_connection.return_value = mock_conn

    # Mock the cursor.fetchall method to return keys
    mock_cursor.fetchall.return_value = [
        ("openai", TEST_OPENAI_KEY),
        ("anthropic", TEST_CLAUDE_KEY)
    ]

    # Call the function
    keys = get_user_api_keys(TEST_USER_ID)

    # Check the result
    assert len(keys) == 2
    assert keys["openai"] == TEST_OPENAI_KEY
    assert keys["anthropic"] == TEST_CLAUDE_KEY

    # Verify the database was called correctly
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    mock_conn.close.assert_called_once()

    # Test with no keys found
    mock_conn.reset_mock()
    mock_cursor.reset_mock()
    mock_cursor.fetchall.return_value = []

    keys = get_user_api_keys(9999)
    assert len(keys) == 0
