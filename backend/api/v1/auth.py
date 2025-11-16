from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.session import get_db
from models.schemas import UserCreate, UserLogin, UserResponse, Token
from services.auth_service import AuthService
from core.dependencies import get_current_user
from models.database import User

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