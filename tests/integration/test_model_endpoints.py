import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.config import set_api_key

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

def test_models_endpoint(auth_headers):
    """Test the /models endpoint"""
    response = client.get("/models", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "models" in data
    assert "huggingface" in data["models"]
    assert "openai" in data["models"]
    assert "claude" in data["models"]
    
    # Check huggingface is always available
    assert data["models"]["huggingface"]["available"] == True

@patch('app.config.set_api_key')
def test_set_api_key_endpoint(mock_set_api_key, auth_headers):
    """Test the /api-keys endpoint"""
    mock_set_api_key.return_value = True
    
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
    mock_set_api_key.assert_called_once_with("openai", "test-key")
    
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

@patch('app.config.set_api_key')
def test_set_api_key_failure(mock_set_api_key, auth_headers):
    """Test failure case for /api-keys endpoint"""
    mock_set_api_key.return_value = False
    
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

def test_summarize_with_model_selection(auth_headers):
    """Test the /summarize endpoint with model selection"""
    # This is a basic test that just checks if the endpoint accepts model parameters
    # We don't actually call the models since they require API keys
    
    response = client.post(
        "/summarize",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "max_length": 500,
            "provider_type": "youtube",
            "model_type": "huggingface",
            "model_name": "facebook/bart-large-cnn"
        },
        headers=auth_headers
    )
    
    # The actual summarization might fail due to YouTube API issues in tests
    # We just want to make sure the endpoint accepts our parameters
    assert response.status_code in [200, 400]
    
    if response.status_code == 400:
        # If it fails, make sure it's not because of invalid parameters
        error = response.json()["detail"]
        assert "model_type" not in error
        assert "model_name" not in error
