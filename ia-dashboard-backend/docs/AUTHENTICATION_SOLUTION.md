# 🔐 Authentication Issue & Solution

## Problem Summary

Your frontend is receiving **401 Unauthorized** when trying to access `/api/v1/chats` because:

1. **No token is being sent**: The frontend is not including the JWT in the `Authorization` header
2. **Mock token instead of real token**: The frontend is using `mock-jwt-1773953130806` instead of obtaining a real JWT from the backend
3. **Missing login step**: The frontend is not calling the `/api/v1/auth/login` endpoint before accessing protected endpoints

## Backend Logs Show This Flow:

```
DEBUG: HTTP request received has_authorization_header=no ← No auth header!
DEBUG: No authorization header provided - allowing anonymous access
DEBUG: Checking if user is authenticated has_user=False
DEBUG: User authentication required but no valid token provided - returning 401 ← Rejected!
```

## Frontend Logs Show This Flow:

```
auth.js:22 Invalid JWT received: mock-jwt-1773953130806 ← Using mock token!
api.js:20 TOKEN: null ← Token is null/undefined!
api.js:32 Skipping invalid token
GET http://localhost:8000/api/v1/chats 401 ← Request fails without token
```

---

## Solution: Real Authentication Flow

### 1️⃣ First: User Must Login

Before accessing any protected endpoints, the frontend **MUST** call the login endpoint:

```javascript
// This is what needs to happen FIRST
async function login(email, password) {
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();
  
  // Save the REAL token
  localStorage.setItem('access_token', data.access_token);
  
  // Now the user is authenticated!
  return data.access_token;
}
```

### 2️⃣ Then: Use Token in All Protected Requests

When accessing protected endpoints, include the token in the Authorization header:

```javascript
// Now when you fetch chats...
async function listChats() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/v1/chats', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`, // ← Include this header!
    },
  });

  return await response.json();
}
```

---

## Testing Your Setup

### Option 1: Run the Test Script

```bash
python scripts/test_auth.py
```

This will:
- ✓ Test that protected endpoints reject unauthenticated requests
- ✓ Test login with demo credentials
- ✓ Test accessing protected endpoints with valid token
- ✓ Test signup with a new account

### Option 2: Test with curl

```bash
# 1. Get a token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPassword123!"}' \
  | jq -r '.access_token')

# 2. Use the token to access protected endpoint
curl -X GET http://localhost:8000/api/v1/chats \
  -H "Authorization: Bearer $TOKEN"
```

### Option 3: Test with Postman/Insomnia

1. **POST**: `http://localhost:8000/api/v1/auth/login`
   - Body: `{ "email": "test@example.com", "password": "TestPassword123!" }`

2. **GET**: `http://localhost:8000/api/v1/chats`
   - Header: `Authorization: Bearer <copy-token-from-step-1>`

---

## Available Authentication Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/auth/login` | Get JWT token with email & password |
| `POST` | `/api/v1/auth/signup` | Create new account & get JWT token |
| `POST` | `/api/v1/auth/refresh` | Get new JWT using refresh token |

### Example: Login Endpoint

**Request:**
```
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "reql_1234567890...",
  "token_type": "bearer",
  "user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "email": "user@example.com"
}
```

---

## Frontend Implementation Checklist

- [ ] Remove all mock JWT tokens from your codebase
- [ ] Implement login page that calls `POST /api/v1/auth/login`
- [ ] Save the `access_token` to localStorage after successful login
- [ ] Create a function that adds `Authorization: Bearer <token>` header to all API requests
- [ ] Redirect to login page if any request returns 401
- [ ] Implement token refresh using `POST /api/v1/auth/refresh` when token expires
- [ ] Clear localStorage when user logs out

---

## How Backend Authentication Works

1. **Token Generation** (Supabase):
   - Backend connects to Supabase Auth
   - User credentials validated
   - Supabase issues real JWT token
   - Backend returns token to frontend

2. **Token Validation** (Backend):
   - Frontend sends JWT in `Authorization: Bearer <token>` header
   - Backend decodes JWT using Supabase secret key
   - If valid, user can access protected endpoints
   - If invalid/missing, returns 401 Unauthorized

3. **Token Expiration**:
   - JWT tokens have expiration time (usually 1 hour)
   - When expired, frontend must use refresh token to get new one
   - If refresh fails, user must login again

---

## Documentation Files

For detailed implementation guide, see:
- **[FRONTEND_AUTH_GUIDE.md](./FRONTEND_AUTH_GUIDE.md)** - Complete frontend implementation guide with code snippets

For test script examples:
- **[scripts/test_auth.py](../scripts/test_auth.py)** - Automated test suite for authentication endpoints

---

## Quick Debugging Checklist

If you still get 401 Unauthorized:

1. ✓ Did the frontend call `/api/v1/auth/login`?
   - Check browser Network tab
   - Should return access_token

2. ✓ Is the token saved to localStorage?
   - Open DevTools → Application → localStorage
   - Should contain `access_token` key

3. ✓ Is the Authorization header being sent?
   - Check browser Network tab for `/api/v1/chats` request
   - Headers tab should show: `Authorization: Bearer eyJ...`

4. ✓ Check backend logs for debug info:
   - `DEBUG: HTTP request received has_authorization_header=no` → Token not sent
   - `DEBUG: JWT format invalid` → Wrong token format
   - `DEBUG: JWT decoding failed` → Token signature invalid

5. ✓ Test the endpoint manually:
   ```bash
   python scripts/test_auth.py
   ```

---

## Contact & Support

Backend Debug Logs Location: Terminal running uvicorn
Look for lines starting with: `DEBUG: ` or `WARNING: `

These logs will tell you exactly what's wrong with authentication requests.
