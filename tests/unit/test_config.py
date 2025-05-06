import pytest
import os
import json
from unittest.mock import patch, mock_open
from app.config import load_config, save_config, get_api_key, set_api_key, get_default_model, DEFAULT_CONFIG

@patch('os.path.exists')
@patch('builtins.open', new_callable=mock_open, read_data=json.dumps({"api_keys": {"test": "test-key"}}))
def test_load_config_existing(mock_file, mock_exists):
    """Test loading configuration from an existing file"""
    mock_exists.return_value = True
    config = load_config()
    assert config["api_keys"]["test"] == "test-key"
    mock_file.assert_called_once()

@patch('os.path.exists')
@patch('app.config.save_config')
def test_load_config_not_existing(mock_save_config, mock_exists):
    """Test loading configuration when file doesn't exist"""
    mock_exists.return_value = False
    mock_save_config.return_value = True
    config = load_config()
    assert config == DEFAULT_CONFIG
    mock_save_config.assert_called_once_with(DEFAULT_CONFIG)

@patch('builtins.open', new_callable=mock_open)
def test_save_config(mock_file):
    """Test saving configuration to file"""
    test_config = {"test": "value"}
    result = save_config(test_config)
    assert result == True
    mock_file.assert_called_once()
    # json.dump() calls write() multiple times, so we can't assert it was called once
    assert mock_file().write.call_count > 0

@patch('app.config.load_config')
@patch('app.config.save_config')
def test_get_api_key(mock_save_config, mock_load_config):
    """Test getting API key from configuration"""
    # Test with key in config
    mock_load_config.return_value = {"api_keys": {"test": "test-key"}}
    key = get_api_key("test")
    assert key == "test-key"
    mock_save_config.assert_not_called()

    # Test with key in environment
    mock_load_config.return_value = {"api_keys": {}}
    with patch.dict(os.environ, {"TEST_API_KEY": "env-key"}):
        key = get_api_key("test")
        assert key == "env-key"
        mock_save_config.assert_called_once()

    # Test with no key
    mock_load_config.reset_mock()
    mock_save_config.reset_mock()
    mock_load_config.return_value = {"api_keys": {}}
    key = get_api_key("test")
    assert key is None
    mock_save_config.assert_not_called()

@patch('app.config.load_config')
@patch('app.config.save_config')
def test_set_api_key(mock_save_config, mock_load_config):
    """Test setting API key in configuration"""
    mock_load_config.return_value = {"api_keys": {}}
    mock_save_config.return_value = True

    with patch.dict(os.environ, {}, clear=True):
        result = set_api_key("test", "new-key")
        assert result == True
        mock_save_config.assert_called_once()
        assert os.environ.get("TEST_API_KEY") == "new-key"

@patch('app.config.load_config')
def test_get_default_model(mock_load_config):
    """Test getting default model from configuration"""
    mock_load_config.return_value = {
        "models": {
            "test": {
                "default": "test-model"
            }
        }
    }

    model = get_default_model("test")
    assert model == "test-model"

    # Test with non-existent model type
    model = get_default_model("nonexistent")
    assert model == ""
