from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from redis_client import redis_client
from .config import SECRET_KEY, ALGORITHM

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        # 1️⃣ Decode JWT first
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email = payload.get("sub")   # you store email here
        user_id = payload.get("id")

        if not email or not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 2️⃣ CHECK REDIS ONLY IF SESSION EXISTS
        # (OTP flow tokens are NOT in Redis)
        redis_keys = redis_client.keys("user_token:*")

        for key in redis_keys:
            stored_jwt = redis_client.get(key)
            if stored_jwt == token:
                # ✅ Session-based token (login / oauth)
                return {
                    "email": email,
                    "id": user_id,
                    "session_key": key.replace("user_token:", "")
                }

        # 3️⃣ If NOT in Redis → allow ONLY for signup / OTP flow
        return {
            "email": email,
            "id": user_id,
            "session_key": None
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
