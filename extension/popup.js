// API endpoints
const API_BASE_URL = 'http://localhost:8000';  // Change this to your API URL
const ENDPOINTS = {
    register: `${API_BASE_URL}/register`,
    login: `${API_BASE_URL}/login`,
    validate: `${API_BASE_URL}/validate`
};

// DOM Elements
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const mainInterface = document.getElementById('mainInterface');
const userNameSpan = document.getElementById('userName');
const loginError = document.getElementById('loginError');
const registerError = document.getElementById('registerError');

// Check authentication status on popup open
document.addEventListener('DOMContentLoaded', async () => {
    const token = await chrome.storage.local.get('token');
    if (token.token) {
        const isValid = await validateToken(token.token);
        if (isValid) {
            showMainInterface();
        } else {
            showLoginForm();
        }
    } else {
        showLoginForm();
    }
});

// Toggle between login and registration forms
function toggleForms() {
    loginForm.classList.toggle('hidden');
    registerForm.classList.toggle('hidden');
    loginError.classList.add('hidden');
    registerError.classList.add('hidden');
}

// Show main interface after successful login
function showMainInterface() {
    loginForm.classList.add('hidden');
    registerForm.classList.add('hidden');
    mainInterface.classList.remove('hidden');
}

// Show login form
function showLoginForm() {
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
    mainInterface.classList.add('hidden');
}

// Handle registration
async function register() {
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;

    try {
        const response = await fetch(ENDPOINTS.register, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Store token
            await chrome.storage.local.set({ token: data.access_token });
            showMainInterface();
        } else {
            registerError.textContent = data.detail || 'Registration failed';
            registerError.classList.remove('hidden');
        }
    } catch (error) {
        registerError.textContent = 'Network error occurred';
        registerError.classList.remove('hidden');
    }
}

// Handle login
async function login() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch(ENDPOINTS.login, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Store token
            await chrome.storage.local.set({ token: data.access_token });
            showMainInterface();
        } else {
            loginError.textContent = data.detail || 'Login failed';
            loginError.classList.remove('hidden');
        }
    } catch (error) {
        loginError.textContent = 'Network error occurred';
        loginError.classList.remove('hidden');
    }
}

// Handle logout
async function logout() {
    await chrome.storage.local.remove('token');
    showLoginForm();
}

// Validate token
async function validateToken(token) {
    try {
        const response = await fetch(`${ENDPOINTS.validate}?token=${token}`);
        return response.ok;
    } catch (error) {
        return false;
    }
} 