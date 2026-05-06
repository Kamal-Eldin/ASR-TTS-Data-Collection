import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from database.session import get_db
from models.database import PasswordResetToken, User
from services.email_service import EmailService
from services.auth_service import hash_password

router = APIRouter(prefix="/api/password-reset", tags=["password-reset"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ValidateTokenRequest(BaseModel):
    token: str


@router.post("/forgot")
def forgot_password(body: ForgotPasswordRequest):
    """Generate a reset token and email it to the user, only if the email matches an account."""
    generic_message = {
        "message": "If we find this email in our data, you should receive a reset password email shortly. Please check your spam folder."
    }

    db = get_db()
    try:
        user = db.query(User).filter(User.email == body.email).first()
        if not user:
            # Same response regardless of match, to avoid leaking which emails are registered
            return generic_message

        # Invalidate any existing unused tokens for this email
        db.query(PasswordResetToken).filter(
            PasswordResetToken.email == body.email,
            PasswordResetToken.used == 0,
        ).update({"used": 1})

        # Create new token (URL-safe, 48 bytes = 64 chars)
        token = secrets.token_urlsafe(48)
        reset = PasswordResetToken(
            email=body.email,
            token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
        )
        db.add(reset)
        db.commit()

        EmailService.send_password_reset_email(body.email, token)

        return generic_message
    except Exception as e:
        db.rollback()
        print(f"[PasswordReset] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process request")
    finally:
        db.close()


@router.post("/validate")
def validate_token(body: ValidateTokenRequest):
    """Check if a reset token is still valid."""
    db = get_db()
    try:
        reset = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == body.token,
            PasswordResetToken.used == 0,
        ).first()

        if not reset or reset.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        return {"valid": True, "email": reset.email}
    finally:
        db.close()


@router.post("/reset")
def reset_password(body: ResetPasswordRequest):
    """Reset the password using the token."""
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    db = get_db()
    try:
        reset = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == body.token,
            PasswordResetToken.used == 0,
        ).first()

        if not reset or reset.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        # Update the user's password
        user = db.query(User).filter(User.email == reset.email).first()
        if not user:
            raise HTTPException(status_code=400, detail="No account found for this email")

        user.hashed_password = hash_password(body.new_password)
        reset.used = 1
        db.commit()

        return {"message": "Password has been reset successfully."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[PasswordReset] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset password")
    finally:
        db.close()
