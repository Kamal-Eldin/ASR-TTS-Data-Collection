import os
import hashlib
import hmac
import secrets
import json
import base64
import time


# JWT config from environment
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me-in-production-" + secrets.token_hex(16))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours default


def hash_password(password: str) -> str:
    """Hash a password with a random salt using PBKDF2-SHA256."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}:{key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        salt, key_hex = stored.split(":")
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_token(user_id: int, email: str) -> str:
    """Create a simple JWT (HS256) without external dependencies."""
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    now = int(time.time())
    payload_data = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + JWT_EXPIRE_MINUTES * 60,
    }
    payload = _b64url_encode(json.dumps(payload_data).encode())
    signature_input = f"{header}.{payload}".encode()
    sig = hmac.new(JWT_SECRET.encode(), signature_input, hashlib.sha256).digest()
    signature = _b64url_encode(sig)
    return f"{header}.{payload}.{signature}"


def verify_token(token: str) -> dict | None:
    """Verify a JWT and return the payload, or None if invalid."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header, payload, signature = parts
        expected_sig = hmac.new(
            JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256
        ).digest()

        if not hmac.compare_digest(_b64url_decode(signature), expected_sig):
            return None

        payload_data = json.loads(_b64url_decode(payload))

        if payload_data.get("exp", 0) < time.time():
            return None

        return payload_data
    except Exception:
        return None
