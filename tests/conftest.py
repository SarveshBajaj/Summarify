"""
Shared test fixtures for all tests.
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

# Create a test client
client = TestClient(app)

@pytest.fixture(scope="session")
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

@pytest.fixture
def mock_provider():
    """Create a mock provider for testing"""
    # Mock the YouTube provider
    with patch("app.providers.YouTubeProvider.extract_video_id", return_value="testid"), \
         patch("app.providers.YouTubeTranscriptApi.get_transcript", return_value=[{"text": "Test transcript", "start": 0, "duration": 1}]), \
         patch("app.providers.pipeline", return_value=MagicMock(return_value=[{"summary_text": "Test summary"}])), \
         patch("app.providers.ContentProvider._validate_summary", return_value=True):
        yield
