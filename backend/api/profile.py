from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from api.dependencies import AuthenticatedUser, get_current_user
from database.connection import SessionLocal
from models.database import User


router = APIRouter(prefix="/api/profile", tags=["profile"])


class LanguagePairSchema(BaseModel):
    language: str = ""
    level: str = ""


class UserProfileResponse(BaseModel):
    id: int
    email: EmailStr
    firstName: str
    lastName: str
    yearOfBirth: str = ""
    gender: str = ""
    country: str = ""
    city: str = ""
    education: str = ""
    profession: str = ""
    languageRelated: str = ""
    nativeLanguage: str = ""
    languagePairs: List[LanguagePairSchema] = []
    system: str = ""
    micType: str = ""


class UpdateProfileRequest(BaseModel):
    firstName: str
    lastName: str
    yearOfBirth: str = ""
    gender: str = ""
    country: str = ""
    city: str = ""
    education: str = ""
    profession: str = ""
    languageRelated: str = ""
    nativeLanguage: str = ""
    languagePairs: List[LanguagePairSchema] = []
    system: str = ""
    micType: str = ""


def _serialize_user(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        firstName=user.first_name,
        lastName=user.last_name,
        yearOfBirth=user.year_of_birth or "",
        gender=user.gender or "",
        country=user.country or "",
        city=user.city or "",
        education=user.education or "",
        profession=user.profession or "",
        languageRelated=user.language_related or "",
        nativeLanguage=user.native_language or "",
        languagePairs=user.language_pairs or [],
        system=user.system or "",
        micType=user.mic_type or "",
    )


@router.get("", response_model=UserProfileResponse)
def get_profile(current_user: AuthenticatedUser = Depends(get_current_user)):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _serialize_user(user)
    finally:
        db.close()


@router.put("", response_model=UserProfileResponse)
def update_profile(
    body: UpdateProfileRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.first_name = body.firstName.strip()
        user.last_name = body.lastName.strip()
        user.year_of_birth = body.yearOfBirth.strip()
        user.gender = body.gender.strip()
        user.country = body.country.strip()
        user.city = body.city.strip()
        user.education = body.education.strip()
        user.profession = body.profession.strip()
        user.language_related = body.languageRelated.strip()
        user.native_language = body.nativeLanguage.strip()
        user.language_pairs = [
            pair.model_dump()
            for pair in body.languagePairs
            if pair.language.strip() or pair.level.strip()
        ]
        user.system = body.system.strip()
        user.mic_type = body.micType.strip()

        db.commit()
        db.refresh(user)
        return _serialize_user(user)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {exc}") from exc
    finally:
        db.close()
