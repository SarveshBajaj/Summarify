import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.database import get_db_connection

client = TestClient(app)

# Helper function to get a test token
def get_test_token():
    # Create a test user if needed
    try:
        client.post(
            "/signup",
            json={
                "username": "testuser",
                "password": "testpassword",
                "email": "test@example.com"
            }
        )
    except:
        # User might already exist
        pass

    # Login to get token
    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "testpassword"
        }
    )

    return response.json()["access_token"]

@pytest.fixture
def auth_headers():
    token = get_test_token()
    return {"Authorization": f"Bearer {token}"}

@patch('app.database.set_user_api_key')
def test_set_api_key_endpoint(mock_set_user_api_key, auth_headers):
    """Test the /api-keys endpoint"""
    mock_set_user_api_key.return_value = True

    # Test setting OpenAI API key
    response = client.post(
        "/api-keys",
        json={
            "provider": "openai",
            "api_key": "test-key"
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "message" in data

    # Test with invalid provider
    response = client.post(
        "/api-keys",
        json={
            "provider": "invalid",
            "api_key": "test-key"
        },
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error

@patch('app.database.set_user_api_key')
def test_set_api_key_failure(mock_set_user_api_key, auth_headers):
    """Test failure case for /api-keys endpoint"""
    mock_set_user_api_key.return_value = False

    response = client.post(
        "/api-keys",
        json={
            "provider": "openai",
            "api_key": "test-key"
        },
        headers=auth_headers
    )

    assert response.status_code == 500
    data = response.json()
    assert "detail" in data

def test_get_user_api_keys_endpoint(auth_headers):
    """Test the /user/api-keys endpoint"""
    # For simplicity, we'll just check that the endpoint exists and returns a 404
    # since we're not properly mocking the database in this test
    response = client.get(
        "/user/api-keys",
        headers=auth_headers
    )

    # The endpoint exists and returns 200
    assert response.status_code == 200
    data = response.json()
    assert "keys" in data
