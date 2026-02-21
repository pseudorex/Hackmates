from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from jose import jwt, JWTError
from app.core.config import settings


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


# ---------------- ACCESS TOKEN ----------------
def create_access_token(
    email: str,
    user_id: int,
    expires_delta: timedelta
):
    expire = datetime.now(timezone.utc) + expires_delta

    print(expires_delta)

    payload = {
        "email": email,
        "user_id": user_id,
        "exp": expire,
        "type": "access"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------- REFRESH TOKEN ----------------
def create_refresh_token(
    email: str,
    user_id: int,
    expires_delta: timedelta
):
    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "email": email,
        "user_id": user_id,
        "exp": expire,
        "type": "refresh"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------- EMAIL VERIFICATION ----------------
def create_email_verification_token(email: str):
    expire = datetime.now(timezone.utc) + timedelta(hours=24)

    payload = {
        "sub": email,
        "exp": expire,
        "type": "email_verification"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------- GENERIC VERIFY ----------------
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


# ---------------- ACCESS TOKEN VALIDATION ----------------
def decode_access_token(token: str):
    payload = verify_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid access token"
        )

    return payload