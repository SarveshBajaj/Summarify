// API Configuration - point to your backend
const API_URL = 'http://localhost:8000';

// Handle authentication and API requests
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'login') {
    login(request.username, request.password)
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true; // Required for async response
  }
  
  if (request.action === 'signup') {
    signup(request.username, request.password, request.email)
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
  
  if (request.action === 'summarize') {
    summarize(request.url, request.maxLength)
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
  
  if (request.action === 'logout') {
    logout();
    sendResponse({ success: true });
  }
});

// Initialize context menu
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'summarize-video',
    title: 'Summarize this YouTube video',
    contexts: ['page'],
    documentUrlPatterns: ['https://*.youtube.com/watch*']
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'summarize-video') {
    chrome.tabs.sendMessage(tab.id, { action: 'getVideoUrl' }, response => {
      if (response && response.url) {
        summarize(response.url)
          .then(summary => {
            // Open popup with the summary
            chrome.runtime.sendMessage({ 
              action: 'showSummary', 
              summary: summary 
            });
          })
          .catch(error => console.error('Error summarizing:', error));
      }
    });
  }
});

// API functions
async function login(username, password) {
  try {
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        username,
        password
      })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }
    
    // Store token in Chrome storage
    chrome.storage.local.set({
      token: data.access_token,
      username: username
    });
    
    return { success: true };
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

async function signup(username, password, email) {
  try {
    const response = await fetch(`${API_URL}/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        password,
        email: email || undefined
      })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Signup failed');
    }
    
    return { success: true };
  } catch (error) {
    console.error('Signup error:', error);
    throw error;
  }
}

async function summarize(url, maxLength = 1000) {
  try {
    // Get token from storage
    const storage = await chrome.storage.local.get(['token']);
    if (!storage.token) {
      throw new Error('You must be logged in to summarize videos');
    }
    
    const response = await fetch(`${API_URL}/summarize`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${storage.token}`
      },
      body: JSON.stringify({
        url,
        max_length: maxLength,
        provider_type: 'youtube'
      })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Summarization failed');
    }
    
    return data;
  } catch (error) {
    console.error('Summarize error:', error);
    throw error;
  }
}

function logout() {
  chrome.storage.local.remove(['token', 'username']);
}
