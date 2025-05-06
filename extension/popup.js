// DOM Elements
const authContainer = document.getElementById('auth-container');
const userContainer = document.getElementById('user-container');
const usernameDisplay = document.getElementById('username-display');
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const logoutBtn = document.getElementById('logout-btn');
const summarizeForm = document.getElementById('summarize-form');
const resultContainer = document.getElementById('result-container');
const loadingIndicator = document.getElementById('loading');
const summaryContent = document.getElementById('summary-content');
const metadataDisplay = document.getElementById('metadata');
const currentVideoContainer = document.getElementById('current-video-container');
const summarizeCurrentBtn = document.getElementById('summarize-current-btn');
const loginError = document.getElementById('login-error');
const signupError = document.getElementById('signup-error');

// Check if user is logged in when popup opens
document.addEventListener('DOMContentLoaded', () => {
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

// Event listeners
loginForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;

  loginError.classList.add('d-none');

  chrome.runtime.sendMessage(
    { action: 'login', username, password },
    (response) => {
      if (response.error) {
        loginError.textContent = response.error;
        loginError.classList.remove('d-none');
      } else {
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
      }
    }
  );
});

signupForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const username = document.getElementById('signup-username').value;
  const password = document.getElementById('signup-password').value;
  const email = document.getElementById('signup-email').value;

  signupError.classList.add('d-none');

  chrome.runtime.sendMessage(
    { action: 'signup', username, password, email },
    (response) => {
      if (response.error) {
        signupError.textContent = response.error;
        signupError.classList.remove('d-none');
      } else {
        // Show success message and switch to login tab
        signupError.textContent = 'Account created successfully! Please log in.';
        signupError.classList.remove('d-none');
        signupError.classList.remove('alert-danger');
        signupError.classList.add('alert-success');

        // Clear form
        document.getElementById('signup-username').value = '';
        document.getElementById('signup-password').value = '';
        document.getElementById('signup-email').value = '';

        // Switch to login tab
        document.getElementById('login-tab').click();
      }
    }
  );
});

logoutBtn.addEventListener('click', () => {
  chrome.runtime.sendMessage({ action: 'logout' }, () => {
    authContainer.classList.remove('d-none');
    userContainer.classList.add('d-none');
    resultContainer.classList.add('d-none');
  });
});

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

// Function to summarize video
function summarizeVideo(url, maxLength) {
  loadingIndicator.classList.remove('d-none');
  resultContainer.classList.remove('d-none');
  summaryContent.textContent = '';
  metadataDisplay.textContent = '';

  chrome.runtime.sendMessage(
    { action: 'summarize', url, maxLength },
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
      Processing time: ${metadata.processing_time_seconds || 'N/A'}s
      ${metadata.valid === false ? ' | <span class="text-warning">Warning: Summary may not be fully accurate</span>' : ''}
    </small>
  `;
}
