import pytest
import os
from app.models import ModelType, get_model, HuggingFaceModel, OpenAIModel, ClaudeModel
from unittest.mock import patch, MagicMock

def test_model_types():
    """Test that all model types are defined correctly"""
    assert ModelType.huggingface == "huggingface"
    assert ModelType.openai == "openai"
    assert ModelType.claude == "claude"

def test_get_model():
    """Test that get_model returns the correct model type"""
    # Test HuggingFace model
    model = get_model(ModelType.huggingface)
    assert isinstance(model, HuggingFaceModel)
    
    # Test OpenAI model with mocked API key
    with patch('app.models.get_api_key', return_value="fake-api-key"):
        model = get_model(ModelType.openai)
        assert isinstance(model, OpenAIModel)
    
    # Test Claude model with mocked API key
    with patch('app.models.get_api_key', return_value="fake-api-key"):
        model = get_model(ModelType.claude)
        assert isinstance(model, ClaudeModel)
    
    # Test invalid model type
    with pytest.raises(NotImplementedError):
        get_model("invalid_model_type")

def test_huggingface_model():
    """Test HuggingFace model initialization and configuration"""
    model = HuggingFaceModel()
    assert model.model_name == "facebook/bart-large-cnn"
    assert model.is_configured() == True  # HuggingFace models are always configured

    # Test with custom model name
    custom_model = HuggingFaceModel(model_name="t5-small")
    assert custom_model.model_name == "t5-small"

@patch('app.models.get_api_key')
def test_openai_model(mock_get_api_key):
    """Test OpenAI model initialization and configuration"""
    # Test with API key
    mock_get_api_key.return_value = "fake-api-key"
    model = OpenAIModel()
    assert model.is_configured() == True
    
    # Test without API key
    mock_get_api_key.return_value = None
    model = OpenAIModel()
    assert model.is_configured() == False

@patch('app.models.get_api_key')
def test_claude_model(mock_get_api_key):
    """Test Claude model initialization and configuration"""
    # Test with API key
    mock_get_api_key.return_value = "fake-api-key"
    model = ClaudeModel()
    assert model.is_configured() == True
    
    # Test without API key
    mock_get_api_key.return_value = None
    model = ClaudeModel()
    assert model.is_configured() == False

@patch('app.models.openai.OpenAI')
@patch('app.models.get_api_key')
def test_openai_summarize(mock_get_api_key, mock_openai):
    """Test OpenAI summarization"""
    # Mock the OpenAI API response
    mock_get_api_key.return_value = "fake-api-key"
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # Mock the completion response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test summary."
    mock_client.chat.completions.create.return_value = mock_response
    
    # Create model and test summarization
    model = OpenAIModel()
    summary = model.summarize("This is a test transcript.", max_length=100)
    
    # Verify the result
    assert summary == "This is a test summary."
    mock_client.chat.completions.create.assert_called_once()

@patch('app.models.anthropic.Anthropic')
@patch('app.models.get_api_key')
def test_claude_summarize(mock_get_api_key, mock_anthropic):
    """Test Claude summarization"""
    # Mock the Claude API response
    mock_get_api_key.return_value = "fake-api-key"
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    
    # Mock the completion response
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "This is a test summary."
    mock_client.messages.create.return_value = mock_response
    
    # Create model and test summarization
    model = ClaudeModel()
    summary = model.summarize("This is a test transcript.", max_length=100)
    
    # Verify the result
    assert summary == "This is a test summary."
    mock_client.messages.create.assert_called_once()
