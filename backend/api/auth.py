from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from database.session import get_db
from models.database import User
from services.auth_service import hash_password, verify_password, create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Request / Response schemas ──────────────────────────────────

class LanguagePairSchema(BaseModel):
    language: str
    level: str


class SignUpRequest(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    yearOfBirth: str
    gender: str
    country: str
    city: str
    education: str
    profession: str
    languageRelated: str
    nativeLanguage: str
    languagePairs: List[LanguagePairSchema]
    password: str
    system: str
    micType: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


# ── Endpoints ───────────────────────────────────────────────────

@router.post("/signup", response_model=AuthResponse)
def signup(body: SignUpRequest):
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    db = get_db()
    try:
        existing = db.query(User).filter(User.email == body.email).first()
        if existing:
            raise HTTPException(status_code=409, detail="An account with this email already exists")

        # Filter out empty language pairs
        lang_pairs = [lp.model_dump() for lp in body.languagePairs if lp.language]

        user = User(
            email=body.email,
            hashed_password=hash_password(body.password),
            first_name=body.firstName,
            last_name=body.lastName,
            year_of_birth=body.yearOfBirth,
            gender=body.gender,
            country=body.country,
            city=body.city,
            education=body.education,
            profession=body.profession,
            language_related=body.languageRelated,
            native_language=body.nativeLanguage,
            language_pairs=lang_pairs,
            system=body.system,
            mic_type=body.micType,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_token(user.id, user.email)

        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[Auth] Signup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create account")
    finally:
        db.close()


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    db = get_db()
    try:
        user = db.query(User).filter(User.email == body.email).first()
        if not user or not verify_password(body.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_token(user.id, user.email)

        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Auth] Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")
    finally:
        db.close()
