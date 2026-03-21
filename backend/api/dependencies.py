from dataclasses import dataclass

from fastapi import Header, HTTPException, Query

from database.connection import SessionLocal
from models.database import User
from services.auth_service import verify_token


@dataclass(slots=True)
class AuthenticatedUser:
    id: int
    email: str
    first_name: str
    last_name: str


def get_current_user(
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> AuthenticatedUser:
    raw_token = None
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ", 1)[1].strip()
    elif token:
        raw_token = token

    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(raw_token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return AuthenticatedUser(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    finally:
        db.close()
