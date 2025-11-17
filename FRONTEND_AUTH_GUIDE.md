# 🔐 Frontend Authentication Guide
## ASR-TTS Data Collection System

---

## 📋 Quick Start

### Base URL
```
Development: http://localhost:8500
```

### Required Headers for Protected Endpoints
```javascript
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json"
}
```

---

## 🚀 Authentication Endpoints

### 1. Register New User
**Endpoint:** `POST /api/v1/auth/register`
**Public:** Yes
**Description:** Create a new user account

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123"  // Min 8 characters
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe"
  }
}
```

**Error Response (400):**
```json
{
  "detail": "Email already registered"
  // or "Username already taken"
  // or "Password must be at least 8 characters long"
}
```

---

### 2. Login
**Endpoint:** `POST /api/v1/auth/login`
**Public:** Yes
**Description:** Login with username or email

**Request Body:**
```json
{
  "username": "johndoe",      // Can be username OR email
  "password": "SecurePass123"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe"
  }
}
```

**Error Response (401):**
```json
{
  "detail": "Incorrect username or password"
}
```

---

### 3. Get Current User
**Endpoint:** `GET /api/v1/auth/me`
**Protected:** Yes 🔒
**Description:** Get current user information

**Success Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

---

## 📂 Protected API Endpoints

> ⚠️ **All endpoints below require authentication token in header**

### Projects

#### Get User's Projects
**Endpoint:** `GET /api/v1/projects`
**Description:** Returns only projects owned by authenticated user

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "Arabic TTS Dataset",
    "is_rtl": true,
    "user_id": 1,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

#### Create Project
**Endpoint:** `POST /api/v1/projects`

**Request Body:**
```json
{
  "name": "My New Project",
  "is_rtl": false
}
```

**Note:** `user_id` is automatically set from JWT token - don't include it in request!

#### Delete Project
**Endpoint:** `DELETE /api/v1/projects/{project_id}`
**Note:** Can only delete your own projects

---

### Recordings

#### Get User's Recordings
**Endpoint:** `GET /api/v1/recordings`
**Query Parameters:**
- `project_id` (optional): Filter by project

**Success Response (200):**
```json
[
  {
    "id": 1,
    "text": "Sample text",
    "filename": "recording_1234.wav",
    "project_id": 1,
    "user_id": 1,
    "recorded_at": "2024-01-15T10:30:00"
  }
]
```

#### Create Recording
**Endpoint:** `POST /api/v1/recordings`
**Content-Type:** `multipart/form-data`

**Form Data:**
```
audio_file: <File>
text: "Transcribed text"
project_id: 1
prompt_id: 5 (optional)
```

**Note:** `user_id` is automatically set from JWT token

---

### Prompts

#### Get Project Prompts
**Endpoint:** `GET /api/v1/prompts?project_id={project_id}`
**Note:** Only returns prompts from user's own projects

#### Create Prompt
**Endpoint:** `POST /api/v1/prompts`

**Request Body:**
```json
{
  "project_id": 1,
  "text": "Please read this sentence",
  "order_index": 1
}
```

---

## 🔄 Frontend Implementation Examples

### 1. Axios Setup with Token
```javascript
import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: 'http://localhost:8500',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 2. Login Flow
```javascript
async function login(username, password) {
  try {
    const response = await api.post('/api/v1/auth/login', {
      username,
      password
    });

    const { access_token, user } = response.data;

    // Store token
    localStorage.setItem('token', access_token);

    // Store user info (optional)
    localStorage.setItem('user', JSON.stringify(user));

    // Redirect to dashboard
    window.location.href = '/dashboard';
  } catch (error) {
    console.error('Login failed:', error.response?.data?.detail);
  }
}
```

### 3. Making Protected Requests
```javascript
// Get user's projects
async function getMyProjects() {
  try {
    const response = await api.get('/api/v1/projects');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch projects:', error);
  }
}

// Create new project
async function createProject(name, isRtl) {
  try {
    const response = await api.post('/api/v1/projects', {
      name,
      is_rtl: isRtl
    });
    return response.data;
  } catch (error) {
    console.error('Failed to create project:', error);
  }
}
```

### 4. Logout
```javascript
function logout() {
  // Clear local storage
  localStorage.removeItem('token');
  localStorage.removeItem('user');

  // Redirect to login
  window.location.href = '/login';
}
```

---

## ⚠️ Important Security Notes

### Do's ✅
1. **Always store token securely** (localStorage or sessionStorage)
2. **Include token in Authorization header** for protected endpoints
3. **Handle 401 responses** by redirecting to login
4. **Validate input** before sending to API
5. **Use HTTPS** in production

### Don'ts ❌
1. **Never store passwords** in localStorage
2. **Never include user_id** in requests (it's extracted from token)
3. **Never share tokens** between users
4. **Never hardcode tokens** in your code
5. **Never ignore SSL certificate errors** in production

---

## 🎯 Common Error Responses

| Status | Meaning | Action |
|--------|---------|--------|
| 400 | Bad Request | Check request format/data |
| 401 | Unauthorized | Token missing/expired - redirect to login |
| 403 | Forbidden | User doesn't have permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., username taken) |
| 422 | Validation Error | Check field requirements |
| 500 | Server Error | Contact backend team |

---

## 📝 Token Information

- **Type:** JWT (JSON Web Token)
- **Expiration:** 24 hours from creation
- **Format:** `Bearer <token>`
- **Storage:** localStorage (recommended) or sessionStorage

### Token Payload Structure
```json
{
  "sub": 1,              // User ID
  "username": "johndoe", // Username
  "exp": 1642339200      // Expiration timestamp
}
```

---

## 🔍 Testing Authentication

### Using cURL
```bash
# Register
curl -X POST http://localhost:8500/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Test1234"}'

# Login
curl -X POST http://localhost:8500/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test1234"}'

# Protected endpoint
curl -X GET http://localhost:8500/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Postman
1. Set request type and URL
2. For login/register: Add JSON body
3. For protected endpoints: Add Authorization header
   - Type: Bearer Token
   - Token: `<your_access_token>`

---

## 🆘 Troubleshooting

### "Invalid token" Error
- Check token hasn't expired (24 hours)
- Verify token format: `Bearer <token>` (note the space)
- Ensure token is being sent in header

### "User not found" Error
- User may have been deleted
- Token might be corrupted
- Try logging in again

### CORS Errors
- Frontend URL must be in backend's allowed origins
- Include credentials in requests if needed

### Can't Access Other Users' Data
- This is by design! Users can only see their own data
- All queries are filtered by user_id from token

---

## 📞 Need Help?

**Backend Team Contact:**
- Authentication issues: Contact backend team
- API bugs: Create issue in repository
- Feature requests: Discuss with team lead

**Quick Links:**
- [Full API Documentation](#)
- [Backend Repository](#)
- [Postman Collection](#)

---

**Last Updated:** January 2024
**API Version:** 1.0.0