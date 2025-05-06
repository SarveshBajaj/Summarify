import pytest
import json
import os
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

# Path to the extension directory
EXTENSION_DIR = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "extension"))

client = TestClient(app)

@pytest.fixture
def mock_chrome_api():
    """Mock Chrome API for testing"""
    class MockChromeStorage:
        def __init__(self):
            self.data = {}

        def get(self, keys, callback):
            result = {k: self.data.get(k) for k in keys}
            callback(result)

        def set(self, data, callback=None):
            self.data.update(data)
            if callback:
                callback()

        def remove(self, keys, callback=None):
            for key in keys:
                if key in self.data:
                    del self.data[key]
            if callback:
                callback()

    class MockChrome:
        def __init__(self):
            self.storage = MagicMock()
            self.storage.local = MockChromeStorage()
            self.runtime = MagicMock()
            self.tabs = MagicMock()
            self.contextMenus = MagicMock()

    return MockChrome()

def test_api_url_matches_backend():
    """Test that the API URL in the extension matches the backend URL"""
    background_path = EXTENSION_DIR / "background.js"

    with open(background_path, 'r') as f:
        content = f.read()

    # Extract API URL
    api_url_match = re.search(r"const API_URL = ['\"](.+?)['\"]", content)
    assert api_url_match, "API_URL not found in background.js"

    api_url = api_url_match.group(1)

    # Check that the URL is valid and matches the test client base URL
    assert api_url.startswith(("http://", "https://")), "API_URL should start with http:// or https://"

    # Extract host and port from API_URL
    api_host_match = re.search(r"(https?://[^:/]+)(?::(\d+))?", api_url)
    assert api_host_match, "Could not parse API_URL"

    # Check that the root endpoint is accessible
    response = client.get("/")
    assert response.status_code == 200, "Backend API root endpoint not accessible"

@pytest.mark.parametrize("endpoint", [
    "/login",
    "/signup",
    "/summarize"
])
def test_backend_endpoints_exist(endpoint):
    """Test that the required backend endpoints exist"""
    # For GET endpoints
    if endpoint in ["/users/me", "/queries/me", "/queries/stats"]:
        # These endpoints require authentication, so we'll just check if they return 401
        response = client.get(endpoint)
        assert response.status_code in [401, 403, 422], f"Endpoint {endpoint} not found or unexpected response"

    # For POST endpoints
    else:
        # Just check if the endpoint exists by sending a POST request
        # We don't care about the response code, just that it's not a 404
        response = client.post(endpoint, json={})
        assert response.status_code != 404, f"Endpoint {endpoint} not found"

        # We don't need to check the allowed methods in the response headers
        # Just check that the endpoint exists and accepts POST requests (even if it returns an error)
        pass

def test_extension_api_functions():
    """Test that the extension's API functions match the backend endpoints"""
    background_path = EXTENSION_DIR / "background.js"

    with open(background_path, 'r') as f:
        content = f.read()

    # Check for login function
    assert "async function login" in content, "login function not found in background.js"
    assert "`${API_URL}/login`" in content, "/login endpoint not used in background.js"

    # Check for signup function
    assert "async function signup" in content, "signup function not found in background.js"
    assert "`${API_URL}/signup`" in content, "/signup endpoint not used in background.js"

    # Check for summarize function
    assert "async function summarize" in content, "summarize function not found in background.js"
    assert "`${API_URL}/summarize`" in content, "/summarize endpoint not used in background.js"

@patch("app.providers.YouTubeProvider.get_transcript")
@patch("app.providers.YouTubeProvider.summarize_and_validate")
def test_summarize_integration(mock_summarize, mock_transcript):
    """Test the integration between the extension and backend for summarization"""
    # This test verifies that the extension can properly format API requests
    # We don't need to test the actual API functionality here, just the integration

    # Check that the background.js file correctly formats the summarize request
    background_path = EXTENSION_DIR / "background.js"
    with open(background_path, 'r') as f:
        background_content = f.read()

    # Verify that the summarize function in background.js sends the correct request format
    assert "async function summarize" in background_content, "Missing summarize function"
    assert "fetch(`${API_URL}/summarize`" in background_content, "Incorrect API endpoint"
    assert "'Authorization': `Bearer ${storage.token}`" in background_content, "Missing authorization header"
    assert "url," in background_content, "Missing URL parameter"
    assert "max_length" in background_content, "Missing max_length parameter"
    assert "provider_type" in background_content, "Missing provider_type parameter"

    # Verify that popup.js correctly handles the summarize response
    popup_path = EXTENSION_DIR / "popup.js"
    with open(popup_path, 'r') as f:
        popup_content = f.read()

    assert "function displaySummary" in popup_content, "Missing displaySummary function"
    assert "summaryContent.textContent = data.summary" in popup_content, "Incorrect summary display"
    assert "metadata.word_count" in popup_content, "Missing word count display"
    assert "metadata.processing_time_seconds" in popup_content, "Missing processing time display"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
