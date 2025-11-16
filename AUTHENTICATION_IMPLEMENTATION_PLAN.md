# 🔐 Authentication Implementation Plan
## ASR-TTS Data Collection System

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Database Changes](#database-changes)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [Step-by-Step Implementation Guide](#step-by-step-implementation-guide)
6. [Testing Checklist](#testing-checklist)

---

## Overview

### Technology Stack
- **Authentication Method**: JWT (JSON Web Tokens)
- **Password Hashing**: bcrypt
- **Frontend State**: React Context API
- **API Structure**: RESTful with /api/v1 prefix
- **Registration**: Open (anyone can sign up)
- **Permissions**: Simple (all users have same permissions)

### Key Features
- User registration with email/username
- JWT-based authentication
- Secure password hashing
- User context isolation (users only see their own data)
- Clean folder structure following best practices

---

## Database Changes

### 1. New User Table

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_username (username)
);
```

### 2. Update Existing Tables

```sql
-- Add user_id to projects table
ALTER TABLE projects
ADD COLUMN user_id INT NOT NULL,
ADD CONSTRAINT fk_projects_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
ADD INDEX idx_projects_user (user_id);

-- Add user_id to prompts table
ALTER TABLE prompts
ADD COLUMN user_id INT NOT NULL,
ADD CONSTRAINT fk_prompts_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
ADD INDEX idx_prompts_user (user_id);

-- Add user_id to recordings table
ALTER TABLE recordings
ADD COLUMN user_id INT NOT NULL,
ADD CONSTRAINT fk_recordings_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
ADD INDEX idx_recordings_user (user_id);

-- Add user_id to settings table (for user-specific settings)
ALTER TABLE settings
ADD COLUMN user_id INT,
ADD CONSTRAINT fk_settings_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
ADD INDEX idx_settings_user (user_id);
```

---

## Backend Implementation

### 1. Install Dependencies

```bash
# Add to requirements.txt
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
email-validator==2.0.0
```

### 2. Core Security Module (`backend/core/security.py`)

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # Move to env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 3. Updated Database Models (`backend/models/database.py`)

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    recordings = relationship("Recording", back_populates="user", cascade="all, delete-orphan")
    prompts = relationship("Prompt", back_populates="creator", cascade="all, delete-orphan")
    settings = relationship("Setting", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)  # Remove unique constraint
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_rtl = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="projects")
    prompts = relationship("Prompt", back_populates="project", cascade="all, delete-orphan")
    recordings = relationship("Recording", back_populates="project", cascade="all, delete-orphan")

class Prompt(Base):
    __tablename__ = 'prompts'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    text = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="prompts")
    project = relationship("Project", back_populates="prompts")
    recordings = relationship("Recording", back_populates="prompt")

class Recording(Base):
    __tablename__ = 'recordings'

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    filename = Column(String(255), unique=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    prompt_id = Column(Integer, ForeignKey('prompts.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Relationships
    user = relationship("User", back_populates="recordings")
    project = relationship("Project", back_populates="recordings")
    prompt = relationship("Prompt", back_populates="recordings")

class Setting(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), index=True)
    value = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))

    # Relationship
    user = relationship("User", back_populates="settings")

class Interaction(Base):
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(255))
    data = Column(Text)  # JSON stored as text
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
```

### 4. Pydantic Schemas (`backend/models/schemas.py`)

```python
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    username: str  # Can be email or username
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

# Updated existing schemas to include user_id
class ProjectCreate(BaseModel):
    name: str
    is_rtl: bool = False
    # user_id will be added automatically from JWT

class ProjectResponse(BaseModel):
    id: int
    name: str
    is_rtl: bool
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
```

### 5. Dependencies (`backend/core/dependencies.py`)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from backend.database.session import get_db
from backend.models.database import User
from backend.core.security import SECRET_KEY, ALGORITHM

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""

    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user

# Optional: For endpoints that might have a user but don't require it
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get the current user if authenticated, otherwise None"""
    try:
        return await get_current_user(credentials, db)
    except:
        return None
```

### 6. Authentication Service (`backend/services/auth_service.py`)

```python
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.models.database import User
from backend.models.schemas import UserCreate, UserLogin
from backend.core.security import verify_password, get_password_hash, create_access_token

class AuthService:
    @staticmethod
    def register(db: Session, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) |
            (User.username == user_data.username)
        ).first()

        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def login(db: Session, user_data: UserLogin) -> dict:
        """Authenticate user and return JWT token"""
        # Find user by username or email
        user = db.query(User).filter(
            (User.username == user_data.username) |
            (User.email == user_data.username)
        ).first()

        if not user or not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )

        # Create access token
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username
            }
        }
```

### 7. Auth API Routes (`backend/api/v1/auth.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.models.schemas import UserCreate, UserLogin, UserResponse, Token
from backend.services.auth_service import AuthService
from backend.core.dependencies import get_current_user
from backend.models.database import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    user = AuthService.register(db, user_data)

    # Auto-login after registration
    login_data = UserLogin(username=user.username, password=user_data.password)
    return AuthService.login(db, login_data)

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login and get JWT token"""
    return AuthService.login(db, user_data)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user
```

### 8. Updated Projects API (`backend/api/v1/projects.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.session import get_db
from backend.models.database import Project, User
from backend.models.schemas import ProjectCreate, ProjectResponse
from backend.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])

@router.get("/", response_model=List[ProjectResponse])
async def get_user_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects for the current user"""
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return projects

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project for the current user"""
    # Check if user already has a project with this name
    existing = db.query(Project).filter(
        Project.name == project.name,
        Project.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a project with this name"
        )

    db_project = Project(
        name=project.name,
        is_rtl=project.is_rtl,
        user_id=current_user.id
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project (only if owned by current user)"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    db.delete(project)
    db.commit()

    return {"message": "Project deleted successfully"}
```

### 9. Updated Main Application (`backend/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import routers
from backend.api.v1 import auth, projects, recordings, exports, settings
from backend.database.connection import engine
from backend.models.database import Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ASR-TTS Data Collection API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(recordings.router)
app.include_router(exports.router)
app.include_router(settings.router)

# Serve static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "api_version": "1.0.0"}
```

---

## Frontend Implementation

### 1. Install Dependencies

```bash
cd frontend
npm install axios
```

### 2. Auth Context (`frontend/src/contexts/AuthContext.tsx`)

```typescript
import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import axios from 'axios';

const BACKEND_URL = 'http://localhost:8500';

interface User {
  id: number;
  email: string;
  username: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Configure axios defaults
axios.defaults.baseURL = BACKEND_URL;

// Add token to all requests if it exists
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on mount
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      fetchUser(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchUser = async (token: string) => {
    try {
      const response = await axios.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      localStorage.removeItem('token');
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      const response = await axios.post('/api/v1/auth/login', {
        username,
        password
      });

      const { access_token, user } = response.data;

      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(user);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const register = async (email: string, username: string, password: string) => {
    try {
      const response = await axios.post('/api/v1/auth/register', {
        email,
        username,
        password
      });

      const { access_token, user } = response.data;

      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(user);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### 3. Login Component (`frontend/src/components/Login.tsx`)

```typescript
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await login(username, password);
      } else {
        await register(email, username, password);
      }
      navigate('/');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {isLogin ? 'Sign in to your account' : 'Create new account'}
          </h2>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {!isLogin && (
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                id="email"
                type="email"
                required={!isLogin}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                placeholder="Email address"
              />
            </div>
          )}

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              id="username"
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
              placeholder="Username"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
              placeholder="Password (min 8 characters)"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Processing...' : (isLogin ? 'Sign in' : 'Sign up')}
            </button>
          </div>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="font-medium text-indigo-600 hover:text-indigo-500"
            >
              {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
```

### 4. Protected Route Component (`frontend/src/components/ProtectedRoute.tsx`)

```typescript
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
```

### 5. Updated App Component (`frontend/src/App.tsx`)

```typescript
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';
import Projects from './components/Projects';
import Recording from './components/Recording';
import Settings from './components/Settings';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/" element={
            <ProtectedRoute>
              <Projects />
            </ProtectedRoute>
          } />

          <Route path="/project/:projectId" element={
            <ProtectedRoute>
              <Recording />
            </ProtectedRoute>
          } />

          <Route path="/settings" element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          } />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
```

---

## Step-by-Step Implementation Guide

### Phase 1: Backend Setup (Day 1)
1. ✅ Stop current Docker containers
2. ✅ Create new folder structure
3. ✅ Install new dependencies
4. ✅ Create security module
5. ✅ Update database models
6. ✅ Create auth service
7. ✅ Create auth API endpoints
8. ✅ Update main.py

### Phase 2: Database Migration (Day 1)
1. ✅ Create migration script
2. ✅ Add User table
3. ✅ Add foreign keys to existing tables
4. ✅ Test database connections

### Phase 3: API Updates (Day 2)
1. ✅ Update all existing endpoints with user context
2. ✅ Add user filtering to queries
3. ✅ Test API endpoints with Postman/curl
4. ✅ Verify data isolation

### Phase 4: Frontend Setup (Day 2)
1. ✅ Create AuthContext
2. ✅ Create Login component
3. ✅ Add protected routes
4. ✅ Update existing components to use auth
5. ✅ Test login/logout flow

### Phase 5: Testing & Deployment (Day 3)
1. ✅ Test user registration
2. ✅ Test user login
3. ✅ Test data isolation
4. ✅ Test token expiration
5. ✅ Update Docker configuration
6. ✅ Deploy and verify

---

## Testing Checklist

### Authentication Tests
- [ ] User can register with unique email/username
- [ ] Duplicate email/username is rejected
- [ ] Password must be at least 8 characters
- [ ] User can login with username or email
- [ ] Invalid credentials are rejected
- [ ] JWT token is returned on successful login
- [ ] Token is valid and contains user info

### Authorization Tests
- [ ] Unauthenticated requests are rejected (401)
- [ ] User can only see their own projects
- [ ] User can only delete their own projects
- [ ] User can only see their own recordings
- [ ] Token expiration is handled properly

### Integration Tests
- [ ] Full registration → login → create project → record → logout flow
- [ ] Data persists after logout/login
- [ ] Multiple users can work independently
- [ ] Database relationships are maintained

### Security Tests
- [ ] Passwords are hashed in database
- [ ] JWT secret is secure
- [ ] SQL injection is prevented
- [ ] XSS is prevented
- [ ] CORS is configured correctly

---

## Migration Script

Create file: `backend/migrate_to_auth.py`

```python
#!/usr/bin/env python3
"""
Migration script to add authentication to existing database
Run this ONCE to update your database schema
"""

import sys
from sqlalchemy import create_engine, text
from backend.config import get_database_url

def migrate_database():
    """Add user table and update existing tables"""

    engine = create_engine(get_database_url())

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Create users table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_email (email),
                    INDEX idx_username (username)
                )
            """))

            # Add user_id to projects
            conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN IF NOT EXISTS user_id INT,
                ADD INDEX IF NOT EXISTS idx_projects_user (user_id)
            """))

            # Add user_id to prompts
            conn.execute(text("""
                ALTER TABLE prompts
                ADD COLUMN IF NOT EXISTS user_id INT,
                ADD INDEX IF NOT EXISTS idx_prompts_user (user_id)
            """))

            # Add user_id to recordings
            conn.execute(text("""
                ALTER TABLE recordings
                ADD COLUMN IF NOT EXISTS user_id INT,
                ADD INDEX IF NOT EXISTS idx_recordings_user (user_id)
            """))

            # Add user_id to settings
            conn.execute(text("""
                ALTER TABLE settings
                ADD COLUMN IF NOT EXISTS user_id INT,
                ADD INDEX IF NOT EXISTS idx_settings_user (user_id)
            """))

            trans.commit()
            print("✅ Migration completed successfully!")

        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    migrate_database()
```

---

## Environment Variables

Add to `.env` file:

```env
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440  # 24 hours

# Existing variables...
MYSQL_HOST=db
MYSQL_PORT=3306
# ... etc
```

---

## Next Steps After Implementation

1. **Enhanced Security**
   - Add refresh tokens
   - Implement password reset via email
   - Add rate limiting
   - Enable 2FA (optional)

2. **User Features**
   - User profile editing
   - Change password
   - Account deletion
   - Activity history

3. **Admin Features**
   - User management dashboard
   - System statistics
   - Bulk operations
   - User roles/permissions

4. **Performance**
   - Add Redis for session caching
   - Implement pagination
   - Add database indexes
   - Query optimization

---

## Troubleshooting

### Common Issues and Solutions

1. **JWT Token Invalid**
   - Check SECRET_KEY matches between frontend/backend
   - Verify token hasn't expired
   - Check Authorization header format

2. **CORS Errors**
   - Verify frontend URL in CORS settings
   - Check credentials are included in requests

3. **Database Foreign Key Errors**
   - Run migration script
   - Check user_id is being passed correctly

4. **Login Failed**
   - Verify password hashing is working
   - Check database connection
   - Verify user exists and is active

---

This completes the authentication implementation plan. Follow the phases sequentially for smooth implementation!