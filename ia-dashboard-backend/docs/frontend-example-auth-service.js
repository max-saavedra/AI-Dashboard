/**
 * Frontend Example: auth-service.js
 * 
 * This shows how your frontend should implement authentication
 * to work with the backend's JWT authentication system.
 * 
 * Copy this logic to your frontend auth.js file.
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

// ============================================
// AUTHENTICATION SERVICE
// ============================================

class AuthService {
  constructor() {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  /**
   * Login with email and password
   * Returns the real JWT token from backend
   */
  async login(email, password) {
    try {
      console.log('🔐 Logging in with email:', email);

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();

      // ✓ Save the REAL token from backend
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('user_email', data.email);

      console.log('✓ Login successful!');
      console.log(`  Token: ${data.access_token.substring(0, 50)}...`);
      console.log(`  User: ${data.email}`);

      return data;
    } catch (error) {
      console.error('✗ Login failed:', error.message);
      throw error;
    }
  }

  /**
   * Signup with email and password
   * Creates a new account and returns JWT
   */
  async signup(email, password) {
    try {
      console.log('📝 Creating new account for:', email);

      const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Signup failed');
      }

      const data = await response.json();

      // ✓ Save the tokens
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('user_email', data.email);

      console.log('✓ Signup and authentication successful!');

      return data;
    } catch (error) {
      console.error('✗ Signup failed:', error.message);
      throw error;
    }
  }

  /**
   * Refresh the access token using refresh token
   * Call this when the access token expires
   */
  async refreshAccessToken() {
    try {
      if (!this.refreshToken) {
        throw new Error('No refresh token available');
      }

      console.log('🔄 Refreshing access token...');

      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: this.refreshToken,
        }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();

      // ✓ Update tokens
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);

      console.log('✓ Token refreshed successfully');

      return data;
    } catch (error) {
      console.error('✗ Token refresh failed:', error.message);
      this.logout();
      throw error;
    }
  }

  /**
   * Logout - clear all tokens and stored data
   */
  logout() {
    console.log('👋 Logging out...');

    this.accessToken = null;
    this.refreshToken = null;

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_email');

    console.log('✓ Logged out');
  }

  /**
   * Check if user is currently authenticated
   */
  isAuthenticated() {
    return !!this.accessToken;
  }

  /**
   * Get current user info
   */
  getCurrentUser() {
    return {
      user_id: localStorage.getItem('user_id'),
      email: localStorage.getItem('user_email'),
    };
  }
}

// ============================================
// API CLIENT
// ============================================

class ApiClient {
  constructor(authService) {
    this.authService = authService;
  }

  /**
   * Internal method to add Authorization header to all requests
   */
  async _fetchWithAuth(url, options = {}) {
    const token = this.authService.accessToken;

    // ✓ Add token to Authorization header
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    } else {
      console.warn('⚠️  No authentication token found');
    }

    const config = {
      ...options,
      headers,
    };

    return fetch(url, config);
  }

  /**
   * GET request with automatic auth header
   */
  async get(endpoint) {
    try {
      const response = await this._fetchWithAuth(`${API_BASE_URL}${endpoint}`);

      if (response.status === 401) {
        console.error('Token expired or invalid');
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`❌ GET ${endpoint} failed:`, error.message);
      throw error;
    }
  }

  /**
   * POST request with automatic auth header
   */
  async post(endpoint, data) {
    try {
      const response = await this._fetchWithAuth(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: JSON.stringify(data),
      });

      if (response.status === 401) {
        console.error('Token expired or invalid');
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`❌ POST ${endpoint} failed:`, error.message);
      throw error;
    }
  }

  /**
   * Protected endpoint: List all chats
   * Requires authentication
   */
  async listChats() {
    console.log('📄 Fetching chats...');
    return this.get('/chats');
  }

  /**
   * Protected endpoint: Delete a chat
   * Requires authentication
   */
  async deleteChat(chatId) {
    console.log(`🗑️  Deleting chat: ${chatId}`);
    return this._fetchWithAuth(`${API_BASE_URL}/chats/${chatId}`, {
      method: 'DELETE',
    });
  }
}

// ============================================
// USAGE EXAMPLE
// ============================================

/*
// In your Vue component or app initialization:

const auth = new AuthService();
const api = new ApiClient(auth);

// 1. USER LOGS IN
async function handleLogin(email, password) {
  try {
    await auth.login(email, password);
    
    // Now you can access protected endpoints
    const chats = await api.listChats();
    console.log('Chats:', chats);
  } catch (error) {
    console.error('Login failed:', error);
  }
}

// 2. USER ACCESSES PROTECTED ENDPOINT
async function loadChats() {
  try {
    // This automatically includes the Authorization header!
    const chats = await api.listChats();
    console.log('Loaded chats:', chats);
  } catch (error) {
    if (error.message === 'Unauthorized') {
      // Token expired, try to refresh
      try {
        await auth.refreshAccessToken();
        // Retry the request
        const chats = await api.listChats();
      } catch {
        // Refresh failed, redirect to login
        window.location.href = '/login';
      }
    }
  }
}

// 3. USER LOGS OUT
async function handleLogout() {
  auth.logout();
  window.location.href = '/login';
}

// 4. ON PAGE LOAD - CHECK IF USER IS LOGGED IN
window.addEventListener('load', () => {
  if (auth.isAuthenticated()) {
    console.log('✓ User is logged in:', auth.getCurrentUser());
    loadChats();
  } else {
    console.log('✗ User not logged in');
    window.location.href = '/login';
  }
});
*/

// Export for use in other files
export { AuthService, ApiClient };
