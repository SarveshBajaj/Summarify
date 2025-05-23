import os
from typing import Dict, Any, Optional
import json
from loguru import logger

# Default configuration
DEFAULT_CONFIG = {
    "api_keys": {
        "openai": "",
        "anthropic": ""
    },
    "models": {
        "huggingface": {
            "default": "facebook/bart-large-cnn"
        },
        "openai": {
            "default": "gpt-3.5-turbo"
        },
        "claude": {
            "default": "claude-3-haiku-20240307"
        }
    }
}

# Path to the config file
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

def load_config() -> Dict[str, Any]:
    """Load configuration from file or create default if not exists"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                logger.info("Configuration loaded from file")
                return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return DEFAULT_CONFIG
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG)
        logger.info("Default configuration created")
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file"""
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info("Configuration saved to file")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return False

def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a specific provider"""
    config = load_config()
    key = config.get("api_keys", {}).get(provider)
    
    # If key is not in config, check environment variables
    if not key:
        env_var_name = f"{provider.upper()}_API_KEY"
        key = os.environ.get(env_var_name)
        
        # If found in environment, update config
        if key:
            config["api_keys"][provider] = key
            save_config(config)
    
    return key

def set_api_key(provider: str, key: str) -> bool:
    """Set API key for a specific provider"""
    config = load_config()
    
    if "api_keys" not in config:
        config["api_keys"] = {}
    
    config["api_keys"][provider] = key
    
    # Also set environment variable
    os.environ[f"{provider.upper()}_API_KEY"] = key
    
    return save_config(config)

def get_default_model(model_type: str) -> str:
    """Get default model for a specific type"""
    config = load_config()
    return config.get("models", {}).get(model_type, {}).get("default", "")

# Initialize configuration on import
config = load_config()

# Set environment variables for API keys
for provider, key in config.get("api_keys", {}).items():
    if key:
        os.environ[f"{provider.upper()}_API_KEY"] = key
        logger.info(f"API key for {provider} loaded from config")
