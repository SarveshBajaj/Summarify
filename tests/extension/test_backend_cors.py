import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cors_headers():
    """Test that CORS headers are properly set for Chrome extensions"""
    # Make a preflight OPTIONS request
    headers = {
        "Origin": "chrome-extension://abcdefghijklmnopqrstuvwxyz",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization",
    }
    
    response = client.options("/", headers=headers)
    
    # Check that the response has the correct CORS headers
    assert response.status_code == 200, "OPTIONS request failed"
    assert "access-control-allow-origin" in response.headers, "Missing access-control-allow-origin header"
    assert "access-control-allow-methods" in response.headers, "Missing access-control-allow-methods header"
    assert "access-control-allow-headers" in response.headers, "Missing access-control-allow-headers header"
    
    # Check that the origin is allowed
    assert response.headers["access-control-allow-origin"] == "*" or \
           "chrome-extension://" in response.headers["access-control-allow-origin"], \
           "Chrome extension origin not allowed"
    
    # Check that the required methods are allowed
    allowed_methods = response.headers["access-control-allow-methods"]
    assert "POST" in allowed_methods, "POST method not allowed"
    assert "GET" in allowed_methods, "GET method not allowed"
    
    # Check that the required headers are allowed
    allowed_headers = response.headers["access-control-allow-headers"]
    assert "content-type" in allowed_headers.lower(), "Content-Type header not allowed"
    assert "authorization" in allowed_headers.lower(), "Authorization header not allowed"

def test_cors_actual_request():
    """Test that an actual request from a Chrome extension works"""
    # Make a GET request with a Chrome extension origin
    headers = {
        "Origin": "chrome-extension://abcdefghijklmnopqrstuvwxyz",
    }
    
    response = client.get("/", headers=headers)
    
    # Check that the response has the correct CORS headers
    assert response.status_code == 200, "GET request failed"
    assert "access-control-allow-origin" in response.headers, "Missing access-control-allow-origin header"
    
    # Check that the origin is allowed
    assert response.headers["access-control-allow-origin"] == "*" or \
           "chrome-extension://" in response.headers["access-control-allow-origin"], \
           "Chrome extension origin not allowed"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
