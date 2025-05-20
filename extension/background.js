// API Configuration - point to your backend
const API_URL = 'http://localhost:8080';

// Handle authentication and API requests
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received message:', request.action);

  if (request.action === 'login') {
    console.log('Background processing login request');
    login(request.username, request.password)
      .then(response => {
        console.log('Login response:', response);
        sendResponse(response);
      })
      .catch(error => {
        console.error('Login error:', error);
        sendResponse({ error: error.message });
      });
    return true; // Required for async response
  }

  if (request.action === 'signup') {
    console.log('Background processing signup request');
    signup(request.username, request.password, request.email)
      .then(response => {
        console.log('Signup response:', response);
        sendResponse(response);
      })
      .catch(error => {
        console.error('Signup error:', error);
        sendResponse({ error: error.message });
      });
    return true;
  }

  if (request.action === 'summarize') {
    summarize(request.url, request.maxLength, request.modelType, request.modelName)
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }

  if (request.action === 'fetchModels') {
    fetchAvailableModels()
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }

  if (request.action === 'fetchUserApiKeys') {
    fetchUserApiKeys()
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }

  if (request.action === 'setApiKey') {
    setApiKey(request.provider, request.apiKey)
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }

  if (request.action === 'test') {
    console.log('Background received test message:', request.message);
    sendResponse({ success: true, message: 'Test response from background script' });
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
  console.log(`Login attempt for user: ${username}`);
  try {
    console.log(`Sending login request to ${API_URL}/login`);
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        username,
        password
      })
    });

    console.log('Login response status:', response.status);
    const data = await response.json();
    console.log('Login response data:', data);

    if (!response.ok) {
      console.error('Login failed:', data.detail);
      throw new Error(data.detail || 'Login failed');
    }

    // Store token in Chrome storage
    console.log('Storing token in Chrome storage');
    chrome.storage.local.set({
      token: data.access_token,
      username: username
    });

    return { success: true, access_token: data.access_token, username: username };
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

async function signup(username, password, email) {
  console.log(`Signup attempt for user: ${username}`);
  try {
    console.log(`Sending signup request to ${API_URL}/signup`);
    const response = await fetch(`${API_URL}/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        password,
        email: email || undefined
      })
    });

    console.log('Signup response status:', response.status);
    const data = await response.json();
    console.log('Signup response data:', data);

    if (!response.ok) {
      console.error('Signup failed:', data.detail);
      throw new Error(data.detail || 'Signup failed');
    }

    return { success: true, access_token: data.access_token, username: username };
  } catch (error) {
    console.error('Signup error:', error);
    throw error;
  }
}

async function summarize(url, maxLength = 1000, modelType = 'huggingface', modelName = null) {
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
        provider_type: 'youtube',
        model_type: modelType,
        model_name: modelName
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

async function fetchAvailableModels() {
  try {
    // Get token from storage
    const storage = await chrome.storage.local.get(['token']);
    if (!storage.token) {
      throw new Error('You must be logged in to fetch models');
    }

    const response = await fetch(`${API_URL}/models`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${storage.token}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch available models');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching models:', error);
    throw error;
  }
}

async function fetchUserApiKeys() {
  try {
    // Get token from storage
    const storage = await chrome.storage.local.get(['token']);
    if (!storage.token) {
      throw new Error('You must be logged in to fetch API keys');
    }

    const response = await fetch(`${API_URL}/user/api-keys`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${storage.token}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch API keys');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching API keys:', error);
    throw error;
  }
}

async function setApiKey(provider, apiKey) {
  try {
    // Get token from storage
    const storage = await chrome.storage.local.get(['token']);
    if (!storage.token) {
      throw new Error('You must be logged in to set API keys');
    }

    const response = await fetch(`${API_URL}/api-keys`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${storage.token}`
      },
      body: JSON.stringify({
        provider,
        api_key: apiKey
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to set API key');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error setting ${provider} API key:`, error);
    throw error;
  }
}
