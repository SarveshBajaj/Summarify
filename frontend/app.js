// API Configuration
const API_URL = 'http://localhost:8000';

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
const loginError = document.getElementById('login-error');
const signupError = document.getElementById('signup-error');

// Auth state
let token = localStorage.getItem('token');
let username = localStorage.getItem('username');

// Check if user is logged in
function checkAuth() {
    if (token) {
        authContainer.classList.add('d-none');
        userContainer.classList.remove('d-none');
        usernameDisplay.textContent = username;
    } else {
        authContainer.classList.remove('d-none');
        userContainer.classList.add('d-none');
        resultContainer.classList.add('d-none');
    }
}

// API Calls
async function login(username, password) {
    try {
        // Create form data for OAuth2 password flow
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            // Don't set Content-Type header - browser will set it with boundary for FormData
            body: formData
        });

        if (!response.ok) {
            let errorMessage = 'Login failed';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
            } catch (e) {
                // If response is not JSON, use status text
                errorMessage = `Login failed: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        token = data.access_token;
        localStorage.setItem('token', token);
        localStorage.setItem('username', username);

        checkAuth();
        loginError.classList.add('d-none');
    } catch (error) {
        loginError.textContent = error.message;
        loginError.classList.remove('d-none');
    }
}

async function signup(username, password, email = null) {
    try {
        const userData = { username, password };
        if (email) userData.email = email;

        const response = await fetch(`${API_URL}/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });

        if (!response.ok) {
            let errorMessage = 'Signup failed';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
            } catch (e) {
                // If response is not JSON, use status text
                errorMessage = `Signup failed: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        token = data.access_token;
        localStorage.setItem('token', token);
        localStorage.setItem('username', username);

        checkAuth();
        signupError.classList.add('d-none');
    } catch (error) {
        signupError.textContent = error.message;
        signupError.classList.remove('d-none');
    }
}

async function summarize(url, maxLength = 1000) {
    try {
        resultContainer.classList.remove('d-none');
        loadingIndicator.classList.remove('d-none');
        summaryContent.innerHTML = '';
        metadataDisplay.innerHTML = '';

        const response = await fetch(`${API_URL}/summarize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                url,
                max_length: maxLength
            })
        });

        if (!response.ok) {
            let errorMessage = 'Summarization failed';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
            } catch (e) {
                // If response is not JSON, use status text
                errorMessage = `Summarization failed: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();

        // Display summary
        summaryContent.textContent = data.summary;

        // Display metadata
        if (data.metadata) {
            // Create validation message with appropriate styling
            let validationClass = data.valid ? 'text-success' : 'text-warning';
            let validationMessage = data.valid ? 'Summary passed validation checks' :
                                               (data.metadata.validation_info || 'Summary may not accurately represent the content');

            const metadataHtml = `
                <div>Word count: ${data.metadata.word_count}</div>
                <div>Processing time: ${data.metadata.processing_time_seconds}s</div>
                <div>Source type: ${data.metadata.source_type}</div>
                <div>Validation: <span class="${validationClass}">${data.valid ? 'Passed' : 'Warning'}</span></div>
                ${!data.valid ? `<div class="${validationClass} small mt-1">${validationMessage}</div>` : ''}
            `;
            metadataDisplay.innerHTML = metadataHtml;
        }
    } catch (error) {
        summaryContent.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    } finally {
        loadingIndicator.classList.add('d-none');
    }
}

// Event Listeners
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    login(username, password);
});

signupForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('signup-username').value;
    const password = document.getElementById('signup-password').value;
    const email = document.getElementById('signup-email').value;
    signup(username, password, email);
});

logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    token = null;
    username = null;
    checkAuth();
});

summarizeForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const url = document.getElementById('youtube-url').value;
    const maxLength = parseInt(document.getElementById('max-length').value);
    summarize(url, maxLength);
});

// Initialize
checkAuth();
