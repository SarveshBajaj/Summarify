// DOM Elements - We'll initialize these after the DOM is fully loaded
let authContainer;
let userContainer;
let usernameDisplay;
let loginForm;
let signupForm;
let logoutBtn;
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

// Initialize everything when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM fully loaded');

  // Initialize all DOM elements
  authContainer = document.getElementById('auth-container');
  userContainer = document.getElementById('user-container');
  usernameDisplay = document.getElementById('username-display');
  loginForm = document.getElementById('login-form');
  signupForm = document.getElementById('signup-form');
  logoutBtn = document.getElementById('logout-btn');
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

  // Signup form submission
  signupForm.addEventListener('submit', (e) => {
    e.preventDefault();
    console.log('Signup form submitted');
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
          loginTab.click();
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

  console.log('All form listeners set up');
}

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
