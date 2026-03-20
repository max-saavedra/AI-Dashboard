# Frontend Authentication Guide

## Problem
Your frontend is using a mock JWT token instead of obtaining a real one from the backend. The backend's `/api/v1/chats` endpoint requires a valid Supabase JWT token.

## Solution: Implement Real Authentication Flow

### Step 1: Call the Login Endpoint

Before accessing protected endpoints, your frontend **must** call the login endpoint to get a real JWT token:

```javascript
// auth.js - Frontend authentication service

async function login(email, password) {
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
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
    throw new Error('Login failed: ' + response.statusText);
  }

  const data = await response.json();
  
  // Save the real JWT token
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  localStorage.setItem('user_id', data.user_id);
  localStorage.setItem('user_email', data.email);
  
  console.log('✓ Login successful! Token saved to localStorage');
  return data;
}
```

### Step 2: Use the Token in API Requests

When making requests to protected endpoints, include the JWT in the `Authorization` header:

```javascript
// api.js - API client

function getAuthHeaders() {
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    console.warn('No JWT token found. Did you login?');
    return {};
  }

  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

async function listChats() {
  const response = await fetch('http://localhost:8000/api/v1/chats', {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (response.status === 401) {
    console.error('Token expired or invalid. Please login again.');
    localStorage.clear();
    window.location.href = '/login'; // Redirect to login page
    return;
  }

  if (!response.ok) {
    throw new Error('Failed to fetch chats: ' + response.statusText);
  }

  return await response.json();
}
```

### Step 3: Handle Token Expiration

Tokens expire after a period. Use the refresh token to get a new one:

```javascript
// auth.js - Token refresh

async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (!refreshToken) {
    console.error('No refresh token available');
    return false;
  }

  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    
    // Update the token
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    console.log('✓ Token refreshed successfully');
    return true;
  } catch (error) {
    console.error('Failed to refresh token:', error);
    localStorage.clear();
    return false;
  }
}
```

## API Endpoints Reference

### Login
```
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}

Response 200:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user_id": "uuid-...",
  "email": "user@example.com"
}
```

### Signup
```
POST /api/v1/auth/signup
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "securePassword123"
}

Response 201:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user_id": "uuid-...",
  "email": "newuser@example.com"
}
```

### Refresh Token
```
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "..."
}

Response 200:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user_id": "uuid-...",
  "email": "user@example.com"
}
```

### Protected Endpoints (require Authorization header)
```
GET /api/v1/chats
Authorization: Bearer <access_token>

DELETE /api/v1/chats/{chat_id}
Authorization: Bearer <access_token>

PATCH /api/v1/chats/{chat_id}
Authorization: Bearer <access_token>
```

## Complete Frontend Flow

```
1. User opens app → Check if token exists in localStorage
   ├─ YES: Try to use it
   └─ NO: Redirect to login page

2. User enters credentials → Call POST /api/v1/auth/login
   ├─ SUCCESS: Save tokens to localStorage → Redirect to dashboard
   └─ FAILED: Show error message

3. User makes API request → Include token in Authorization header
   ├─ 200-399: Success, use response
   ├─ 401: Token expired → Call POST /api/v1/auth/refresh
   └─ 401 again: Login required → Redirect to login

4. User logs out → Clear localStorage → Redirect to login
```

## Testing the Endpoint Locally

Using curl:
```bash
# Login (get token)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Use token to access protected endpoint
curl -X GET http://localhost:8000/api/v1/chats \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

Using Postman or Insomnia:
1. Create a POST request to `http://localhost:8000/api/v1/auth/login`
2. Set body to JSON with email and password
3. Copy the `access_token` from response
4. Create a GET request to `http://localhost:8000/api/v1/chats`
5. In Headers, add: `Authorization: Bearer <paste-token-here>`

## Troubleshooting

### "Invalid JWT received: mock-jwt..."
**Problem**: Your frontend is using a hardcoded mock token.
**Solution**: Remove the mock token and call the real login endpoint instead.

### "TOKEN: null"
**Problem**: The token is not being saved to localStorage.
**Solution**: Ensure you're calling the login endpoint correctly and parsing the response.

### "401 Unauthorized"
**Problem**: The Authorization header is not being sent or the token is invalid/expired.
**Solution**: 
- Check that `access_token` exists in localStorage
- Check that the Authorization header is correctly formatted: `Bearer <token>`
- Try refreshing the token using the refresh endpoint
- Check the backend logs for detailed error messages

### Backend Logs Show Details
Check the backend logs (terminal running uvicorn) for debug info:
```
DEBUG: HTTP request received has_authorization_header=no
DEBUG: No authorization header provided - allowing anonymous access
DEBUG: User authentication required but no valid token provided - returning 401
```

This means your frontend is not sending the Authorization header.
