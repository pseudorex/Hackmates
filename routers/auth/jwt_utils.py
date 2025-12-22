from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from jose import jwt, JWTError
from .config import SECRET_KEY, ALGORITHM


def create_access_token(email: str, user_id: int, expires_delta: timedelta):
    payload = {
        "email": email,
        "user_id": user_id,
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_email_verification_token(email: str):
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": email,
        "exp": expire
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
