import pytest
import os
import json
import re
from pathlib import Path

# Path to the extension directory
EXTENSION_DIR = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "extension"))

def test_manifest_structure():
    """Test that the manifest.json file has the required fields"""
    manifest_path = EXTENSION_DIR / "manifest.json"
    assert manifest_path.exists(), "manifest.json file not found"
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Check required fields
    assert "manifest_version" in manifest, "Missing manifest_version"
    assert "name" in manifest, "Missing name"
    assert "version" in manifest, "Missing version"
    assert "description" in manifest, "Missing description"
    assert "permissions" in manifest, "Missing permissions"
    assert "action" in manifest, "Missing action"
    
    # Check permissions
    required_permissions = ["storage", "activeTab", "contextMenus"]
    for perm in required_permissions:
        assert perm in manifest["permissions"], f"Missing permission: {perm}"
    
    # Check action
    assert "default_popup" in manifest["action"], "Missing default_popup in action"
    assert "default_icon" in manifest["action"], "Missing default_icon in action"
    
    # Check content scripts
    assert "content_scripts" in manifest, "Missing content_scripts"
    assert len(manifest["content_scripts"]) > 0, "No content scripts defined"
    assert "matches" in manifest["content_scripts"][0], "Missing matches in content script"
    assert "js" in manifest["content_scripts"][0], "Missing js in content script"
    
    # Check background script
    assert "background" in manifest, "Missing background"
    assert "service_worker" in manifest["background"], "Missing service_worker in background"

def test_html_files():
    """Test that HTML files exist and have required elements"""
    popup_path = EXTENSION_DIR / "popup.html"
    assert popup_path.exists(), "popup.html file not found"
    
    with open(popup_path, 'r') as f:
        content = f.read()
    
    # Check for required elements
    assert "<html" in content, "Missing html tag"
    assert "<head" in content, "Missing head tag"
    assert "<body" in content, "Missing body tag"
    assert "popup.js" in content, "Missing reference to popup.js"
    assert "popup.css" in content, "Missing reference to popup.css"
    
    # Check for required containers
    assert 'id="auth-container"' in content, "Missing auth-container"
    assert 'id="user-container"' in content, "Missing user-container"
    assert 'id="result-container"' in content, "Missing result-container"

def test_js_files():
    """Test that JS files exist and have required functionality"""
    background_path = EXTENSION_DIR / "background.js"
    popup_path = EXTENSION_DIR / "popup.js"
    content_path = EXTENSION_DIR / "content.js"
    
    assert background_path.exists(), "background.js file not found"
    assert popup_path.exists(), "popup.js file not found"
    assert content_path.exists(), "content.js file not found"
    
    # Check background.js
    with open(background_path, 'r') as f:
        background_content = f.read()
    
    assert "chrome.runtime.onMessage.addListener" in background_content, "Missing message listener in background.js"
    assert "chrome.contextMenus.create" in background_content, "Missing context menu creation in background.js"
    assert "async function login" in background_content, "Missing login function in background.js"
    assert "async function summarize" in background_content, "Missing summarize function in background.js"
    
    # Check popup.js
    with open(popup_path, 'r') as f:
        popup_content = f.read()
    
    assert "document.addEventListener('DOMContentLoaded'" in popup_content, "Missing DOMContentLoaded listener in popup.js"
    assert "chrome.storage.local.get" in popup_content, "Missing storage access in popup.js"
    assert "function summarizeVideo" in popup_content, "Missing summarizeVideo function in popup.js"
    
    # Check content.js
    with open(content_path, 'r') as f:
        content_content = f.read()
    
    assert "chrome.runtime.onMessage.addListener" in content_content, "Missing message listener in content.js"
    assert "function addSummarizeButton" in content_content, "Missing addSummarizeButton function in content.js"

def test_css_file():
    """Test that CSS file exists and has required styles"""
    css_path = EXTENSION_DIR / "popup.css"
    assert css_path.exists(), "popup.css file not found"
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Check for basic styles
    assert "body" in content, "Missing body style"
    assert "width:" in content, "Missing width definition"
    assert "#summary-content" in content, "Missing #summary-content style"

def test_api_url_configuration():
    """Test that the API URL is properly configured"""
    background_path = EXTENSION_DIR / "background.js"
    
    with open(background_path, 'r') as f:
        content = f.read()
    
    # Extract API URL
    api_url_match = re.search(r"const API_URL = ['\"](.+?)['\"]", content)
    assert api_url_match, "API_URL not found in background.js"
    
    api_url = api_url_match.group(1)
    assert api_url, "API_URL is empty"
    
    # Check that the URL is valid
    assert api_url.startswith(("http://", "https://")), "API_URL should start with http:// or https://"

def test_icons_exist():
    """Test that icon files exist"""
    icon_sizes = [16, 48, 128]
    
    for size in icon_sizes:
        icon_path = EXTENSION_DIR / "icons" / f"icon{size}.png"
        assert icon_path.exists(), f"Icon file icon{size}.png not found"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
