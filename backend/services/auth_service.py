from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.database import User
from models.schemas import UserCreate, UserLogin
from core.security import verify_password, get_password_hash, create_access_token
from services.settings_service import SettingsService

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

        # Create default settings for the new user
        SettingsService.create_default_settings(db_user.id, db)  # type: ignore[arg-type]

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
            data={"sub": str(user.id), "username": user.username}
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