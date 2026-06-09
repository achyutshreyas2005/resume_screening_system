"""
auth.py
-------
Handles JWT token creation, password hashing, and user verification.
"""

from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt

# ── Config ─────────────────────────────────────────────────────────────────────
SECRET_KEY           = "your-super-secret-key-change-this-in-production"
ALGORITHM            = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 8


def hash_password(password: str) -> str:
    """Hash a plain password."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Check plain password against hashed."""
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


def create_token(data: dict) -> str:
    """Create a JWT token."""
    to_encode = data.copy()
    expire    = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None