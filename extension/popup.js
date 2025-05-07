// DOM Elements - We'll initialize these after the DOM is fully loaded
let authContainer;
let userContainer;
let usernameDisplay;
let loginForm;
let signupForm;
let logoutBtn;
let settingsBtn;
let summarizeForm;
let resultContainer;
let loadingIndicator;
let summaryContent;
let metadataDisplay;
let currentVideoContainer;
let summarizeCurrentBtn;
let loginError;
let signupError;
let loginTab;
let signupTab;
let copySummaryBtn;

// Settings Modal Elements
let settingsModal;
let apiKeysLoading;
let apiKeysContainer;
let openaiKeyForm;
let claudeKeyForm;
let openaiApiKey;
let claudeApiKey;
let openaiStatusBadge;
let claudeStatusBadge;

// Model selection elements
let modelTypeSelect;
let modelNameSelect;
let modelNameContainer;

// Available models from the server
let availableModels = {};

// Fetch available models
function fetchAvailableModels() {
  chrome.runtime.sendMessage({ action: 'fetchModels' }, (response) => {
    if (response.error) {
      console.error('Error fetching models:', response.error);
    } else {
      availableModels = response.models || {};
      updateModelSelectionUI();
    }
  });
}

// Fetch user's API keys
function fetchUserApiKeys() {
  apiKeysLoading.classList.remove('d-none');
  apiKeysContainer.classList.add('d-none');

  chrome.runtime.sendMessage({ action: 'fetchUserApiKeys' }, (response) => {
    if (response.error) {
      console.error('Error fetching API keys:', response.error);
    } else {
      // Update UI based on API keys
      response.keys.forEach(key => {
        if (key.provider === 'openai') {
          updateApiKeyStatus('openai', key.has_key, key.last_updated);
        } else if (key.provider === 'anthropic') {
          updateApiKeyStatus('claude', key.has_key, key.last_updated);
        }
      });
    }

    apiKeysLoading.classList.add('d-none');
    apiKeysContainer.classList.remove('d-none');
  });
}

// Update API key status in UI
function updateApiKeyStatus(provider, hasKey, lastUpdated) {
  const badge = provider === 'openai' ? openaiStatusBadge : claudeStatusBadge;

  if (hasKey) {
    badge.textContent = 'Configured';
    badge.classList.remove('bg-secondary', 'bg-danger');
    badge.classList.add('bg-success');

    // Add last updated info if available
    if (lastUpdated) {
      const date = new Date(lastUpdated.replace(' ', 'T'));
      badge.title = `Last updated: ${date.toLocaleString()}`;
    }
  } else {
    badge.textContent = 'Not Configured';
    badge.classList.remove('bg-success');
    badge.classList.add('bg-secondary');
    badge.title = '';
  }
}

// Set API key
async function setApiKey(provider, apiKey) {
  try {
    const response = await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { action: 'setApiKey', provider, apiKey },
        (response) => {
          if (response.error) {
            reject(new Error(response.error));
          } else {
            resolve(response);
          }
        }
      );
    });

    // Refresh available models
    fetchAvailableModels();

    // Refresh user API keys
    fetchUserApiKeys();

    return true;
  } catch (error) {
    console.error(`Error setting ${provider} API key:`, error);
    alert(`Error setting API key: ${error.message}`);
    return false;
  }
}

// Update model selection UI
function updateModelSelectionUI() {
  // Update the model type dropdown based on what's available
  for (const option of modelTypeSelect.options) {
    const modelType = option.value;
    if (modelType !== 'huggingface') { // HuggingFace is always available locally
      const isAvailable = availableModels[modelType]?.available;
      const userConfigured = availableModels[modelType]?.user_configured;

      // Reset the option text to remove any previous annotations
      if (modelType === 'openai') {
        option.text = 'OpenAI';
      } else if (modelType === 'claude') {
        option.text = 'Claude';
      }

      option.disabled = !isAvailable;

      if (!isAvailable) {
        option.text += ' (API key required)';
      } else if (userConfigured) {
        option.text += ' (Your key)';
      }
    }
  }

  // Set up the model name dropdown based on the selected model type
  updateModelNameOptions();
}

// Update model name options based on selected model type
function updateModelNameOptions() {
  const selectedModelType = modelTypeSelect.value;

  // Define model options
  const modelOptions = {
    huggingface: [
      { value: 'facebook/bart-large-cnn', label: 'BART Large CNN (Default)' },
      { value: 't5-small', label: 'T5 Small (Faster)' }
    ],
    openai: [
      { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo (Default)' },
      { value: 'gpt-4', label: 'GPT-4 (More Capable)' },
      { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' }
    ],
    claude: [
      { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku (Default, Fastest)' },
      { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet (Balanced)' },
      { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus (Most Capable)' }
    ]
  };

  // Clear existing options
  modelNameSelect.innerHTML = '';

  // Get options for the selected model type
  const options = modelOptions[selectedModelType] || [];

  // Add options to the select element
  options.forEach(option => {
    const optionElement = document.createElement('option');
    optionElement.value = option.value;
    optionElement.textContent = option.label;
    modelNameSelect.appendChild(optionElement);
  });

  // Show/hide the model name container based on whether there are options
  if (options.length > 0) {
    modelNameContainer.classList.remove('d-none');
  } else {
    modelNameContainer.classList.add('d-none');
  }

  // Show/hide API key warning for non-HuggingFace models
  if (selectedModelType !== 'huggingface') {
    const isAvailable = availableModels[selectedModelType]?.available;
    apiKeyWarning.classList.toggle('d-none', isAvailable);
  } else {
    apiKeyWarning.classList.add('d-none');
  }
}

// Initialize everything when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM fully loaded');

  // Add direct click handlers to buttons for debugging
  document.getElementById('login-button')?.addEventListener('click', function(e) {
    console.log('Login button clicked directly');
    alert('Login button clicked!');
    // Don't prevent default - let the form submission happen
  });

  document.getElementById('signup-button')?.addEventListener('click', function(e) {
    console.log('Signup button clicked directly');
    // Don't prevent default - let the form submission happen
  });

  // Add debug button handler
  document.getElementById('debug-btn')?.addEventListener('click', function() {
    console.log('Debug button clicked');
    const debugConsole = document.getElementById('debug-console');
    if (debugConsole) {
      debugConsole.style.display = debugConsole.style.display === 'none' ? 'block' : 'none';
    }

    // Also show a test message in the console
    console.log('Debug test message - Chrome runtime:', chrome.runtime);

    // Try a test message to the background script
    chrome.runtime.sendMessage(
      { action: 'test', message: 'Test message from popup' },
      (response) => {
        console.log('Test message response:', response);
      }
    );
  });

  // Initialize all DOM elements
  authContainer = document.getElementById('auth-container');
  userContainer = document.getElementById('user-container');
  usernameDisplay = document.getElementById('username-display');
  loginForm = document.getElementById('login-form');
  signupForm = document.getElementById('signup-form');
  logoutBtn = document.getElementById('logout-btn');
  settingsBtn = document.getElementById('settings-btn');
  summarizeForm = document.getElementById('summarize-form');
  resultContainer = document.getElementById('result-container');
  loadingIndicator = document.getElementById('loading');
  summaryContent = document.getElementById('summary-content');
  metadataDisplay = document.getElementById('metadata');
  currentVideoContainer = document.getElementById('current-video-container');
  summarizeCurrentBtn = document.getElementById('summarize-current-btn');
  loginError = document.getElementById('login-error');
  signupError = document.getElementById('signup-error');
  loginTab = document.getElementById('login-tab');
  signupTab = document.getElementById('signup-tab');
  copySummaryBtn = document.getElementById('copy-summary-btn');

  // Initialize settings modal elements
  settingsModal = new bootstrap.Modal(document.getElementById('settings-modal'));
  apiKeysLoading = document.getElementById('api-keys-loading');
  apiKeysContainer = document.getElementById('api-keys-container');
  openaiKeyForm = document.getElementById('openai-key-form');
  claudeKeyForm = document.getElementById('claude-key-form');
  openaiApiKey = document.getElementById('openai-api-key');
  claudeApiKey = document.getElementById('claude-api-key');
  openaiStatusBadge = document.getElementById('openai-status-badge');
  claudeStatusBadge = document.getElementById('claude-status-badge');

  // Initialize model selection elements
  modelTypeSelect = document.getElementById('model-type');
  modelNameSelect = document.getElementById('model-name');
  modelNameContainer = document.getElementById('model-name-container');

  // Initialize Bootstrap tabs manually
  loginTab.addEventListener('click', (e) => {
    e.preventDefault();
    document.querySelector('#login').classList.add('show', 'active');
    document.querySelector('#signup').classList.remove('show', 'active');
    loginTab.classList.add('active');
    signupTab.classList.remove('active');
  });

  signupTab.addEventListener('click', (e) => {
    e.preventDefault();
    document.querySelector('#login').classList.remove('show', 'active');
    document.querySelector('#signup').classList.add('show', 'active');
    loginTab.classList.remove('active');
    signupTab.classList.add('active');
  });

  // Set up form event listeners
  setupFormListeners();

  // Add direct form submission handlers as a backup
  document.getElementById('login-form')?.addEventListener('submit', function(e) {
    console.log('Login form submitted directly');
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    // Show a message
    const loginError = document.getElementById('login-error');
    loginError.textContent = 'Direct login attempt...';
    loginError.classList.remove('d-none');

    // Send message directly
    chrome.runtime.sendMessage(
      { action: 'login', username, password },
      (response) => {
        console.log('Direct login response:', response);
        loginError.textContent = response?.error || 'Login successful!';
      }
    );
  });

  document.getElementById('signup-form')?.addEventListener('submit', function(e) {
    console.log('Signup form submitted directly');
    e.preventDefault();
    const username = document.getElementById('signup-username').value;
    const password = document.getElementById('signup-password').value;
    const email = document.getElementById('signup-email').value;

    // Show a message
    const signupError = document.getElementById('signup-error');
    signupError.textContent = 'Direct signup attempt...';
    signupError.classList.remove('d-none');

    // Send message directly
    chrome.runtime.sendMessage(
      { action: 'signup', username, password, email },
      (response) => {
        console.log('Direct signup response:', response);
        signupError.textContent = response?.error || 'Signup successful!';
      }
    );
  });

  // Check if user is logged in
  chrome.storage.local.get(['token', 'username'], (result) => {
    if (result.token && result.username) {
      authContainer.classList.add('d-none');
      userContainer.classList.remove('d-none');
      usernameDisplay.textContent = result.username;

      // Check if current tab is YouTube
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const currentUrl = tabs[0].url;
        if (currentUrl && currentUrl.includes('youtube.com/watch')) {
          currentVideoContainer.classList.remove('d-none');
          document.getElementById('youtube-url').value = currentUrl;
        }
      });

      // Fetch available models
      fetchAvailableModels();

      // Fetch user's API keys
      fetchUserApiKeys();
    } else {
      authContainer.classList.remove('d-none');
      userContainer.classList.add('d-none');
    }
  });

  // Check for any pending summaries
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'showSummary' && request.summary) {
      displaySummary(request.summary);
    }
  });
});

// Set up all form event listeners
function setupFormListeners() {
  console.log('Setting up form listeners');

  // Login form submission
  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    console.log('Login form submitted');
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    console.log(`Attempting to login user: ${username}`);

    loginError.classList.add('d-none');

    // Add a visible message for debugging
    loginError.textContent = 'Sending login request...';
    loginError.classList.remove('d-none');
    loginError.classList.remove('alert-danger');
    loginError.classList.add('alert-info');

    console.log('Sending login message to background script');
    chrome.runtime.sendMessage(
      { action: 'login', username, password },
      (response) => {
        console.log('Received login response:', response);

        if (response && response.error) {
          console.error('Login error:', response.error);
          loginError.textContent = response.error;
          loginError.classList.remove('alert-info');
          loginError.classList.add('alert-danger');
          loginError.classList.remove('d-none');
        } else if (response && response.success) {
          console.log('Login successful');
          loginError.textContent = 'Login successful!';
          loginError.classList.remove('alert-danger');
          loginError.classList.add('alert-success');

          // Refresh UI after a short delay
          setTimeout(() => {
            // Refresh UI
            authContainer.classList.add('d-none');
            userContainer.classList.remove('d-none');
            usernameDisplay.textContent = username;

            // Check if current tab is YouTube
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
              const currentUrl = tabs[0].url;
              if (currentUrl && currentUrl.includes('youtube.com/watch')) {
                currentVideoContainer.classList.remove('d-none');
                document.getElementById('youtube-url').value = currentUrl;
              }
            });
          }, 1000);
        } else {
          console.error('Unexpected login response:', response);
          loginError.textContent = 'Unexpected error. Please try again.';
          loginError.classList.remove('alert-info');
          loginError.classList.add('alert-danger');
          loginError.classList.remove('d-none');
        }
      }
    );
  });

  // Signup form submission
  signupForm.addEventListener('submit', (e) => {
    e.preventDefault();
    console.log('Signup form submitted');
    const username = document.getElementById('signup-username').value;
    const password = document.getElementById('signup-password').value;
    const email = document.getElementById('signup-email').value;
    console.log(`Attempting to signup user: ${username}`);

    signupError.classList.add('d-none');

    // Add a visible message for debugging
    signupError.textContent = 'Sending signup request...';
    signupError.classList.remove('d-none');
    signupError.classList.remove('alert-danger');
    signupError.classList.add('alert-info');

    console.log('Sending signup message to background script');
    chrome.runtime.sendMessage(
      { action: 'signup', username, password, email },
      (response) => {
        console.log('Received signup response:', response);

        if (response && response.error) {
          console.error('Signup error:', response.error);
          signupError.textContent = response.error;
          signupError.classList.remove('alert-info');
          signupError.classList.add('alert-danger');
          signupError.classList.remove('d-none');
        } else if (response && response.success) {
          console.log('Signup successful');
          // Show success message and switch to login tab
          signupError.textContent = 'Account created successfully! Please log in.';
          signupError.classList.remove('alert-info');
          signupError.classList.remove('alert-danger');
          signupError.classList.add('alert-success');

          // Clear form
          document.getElementById('signup-username').value = '';
          document.getElementById('signup-password').value = '';
          document.getElementById('signup-email').value = '';

          // Switch to login tab after a short delay
          setTimeout(() => {
            loginTab.click();
          }, 1000);
        } else {
          console.error('Unexpected signup response:', response);
          signupError.textContent = 'Unexpected error. Please try again.';
          signupError.classList.remove('alert-info');
          signupError.classList.add('alert-danger');
          signupError.classList.remove('d-none');
        }
      }
    );
  });

  // Logout button
  logoutBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'logout' }, () => {
      authContainer.classList.remove('d-none');
      userContainer.classList.add('d-none');
      resultContainer.classList.add('d-none');
    });
  });

  // Settings button
  settingsBtn.addEventListener('click', () => {
    settingsModal.show();
  });

  // OpenAI API key form
  openaiKeyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const apiKey = openaiApiKey.value.trim();
    if (!apiKey) {
      alert('Please enter a valid API key');
      return;
    }

    const success = await setApiKey('openai', apiKey);
    if (success) {
      openaiApiKey.value = '';
      alert('OpenAI API key saved successfully');
    }
  });

  // Claude API key form
  claudeKeyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const apiKey = claudeApiKey.value.trim();
    if (!apiKey) {
      alert('Please enter a valid API key');
      return;
    }

    const success = await setApiKey('anthropic', apiKey);
    if (success) {
      claudeApiKey.value = '';
      alert('Claude API key saved successfully');
    }
  });

  // Summarize form
  summarizeForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const url = document.getElementById('youtube-url').value;
    const maxLength = parseInt(document.getElementById('max-length').value);

    if (!url) {
      alert('Please enter a YouTube URL');
      return;
    }

    summarizeVideo(url, maxLength);
  });

  // Handle summarize current video button
  summarizeCurrentBtn.addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const currentUrl = tabs[0].url;
      const maxLength = parseInt(document.getElementById('max-length').value);
      summarizeVideo(currentUrl, maxLength);
    });
  });

  // Handle copy summary button
  copySummaryBtn.addEventListener('click', () => {
    const summaryText = summaryContent.textContent;
    if (summaryText) {
      navigator.clipboard.writeText(summaryText)
        .then(() => {
          // Change button text temporarily to show success
          const originalText = copySummaryBtn.textContent;
          copySummaryBtn.textContent = 'Copied!';
          copySummaryBtn.classList.remove('btn-outline-primary');
          copySummaryBtn.classList.add('btn-success');

          // Reset button after 2 seconds
          setTimeout(() => {
            copySummaryBtn.textContent = originalText;
            copySummaryBtn.classList.remove('btn-success');
            copySummaryBtn.classList.add('btn-outline-primary');
          }, 2000);
        })
        .catch(err => {
          console.error('Failed to copy text: ', err);
          alert('Failed to copy summary to clipboard');
        });
    }
  });

  // Model type selection change
  modelTypeSelect.addEventListener('change', () => {
    updateModelNameOptions();
  });

  // Initialize model name options
  updateModelNameOptions();

  console.log('All form listeners set up');
}

// Function to summarize video
function summarizeVideo(url, maxLength) {
  loadingIndicator.classList.remove('d-none');
  resultContainer.classList.remove('d-none');
  summaryContent.textContent = '';
  metadataDisplay.textContent = '';

  // Get selected model type and name
  const modelType = modelTypeSelect.value;
  const modelName = modelNameSelect.value || null;

  // Check if the model is available
  if (modelType !== 'huggingface') {
    const isAvailable = availableModels[modelType]?.available;
    if (!isAvailable) {
      loadingIndicator.classList.add('d-none');
      summaryContent.textContent = `Error: ${modelType} API key is required. Please set it in Settings.`;
      return;
    }
  }

  chrome.runtime.sendMessage(
    { action: 'summarize', url, maxLength, modelType, modelName },
    (response) => {
      loadingIndicator.classList.add('d-none');

      if (response.error) {
        summaryContent.textContent = `Error: ${response.error}`;
      } else {
        displaySummary(response);
      }
    }
  );
}

// Display summary in the UI
function displaySummary(data) {
  resultContainer.classList.remove('d-none');
  loadingIndicator.classList.add('d-none');

  summaryContent.textContent = data.summary;

  // Format metadata
  const metadata = data.metadata || {};
  metadataDisplay.innerHTML = `
    <small>
      Word count: ${metadata.word_count || 'N/A'} |
      Processing time: ${metadata.processing_time_seconds || 'N/A'}s |
      Model: ${metadata.model_type || 'huggingface'} ${metadata.model_name ? `(${metadata.model_name})` : ''}
      ${metadata.valid === false ? ' | <span class="text-warning">Warning: Summary may not be fully accurate</span>' : ''}
    </small>
  `;
}
