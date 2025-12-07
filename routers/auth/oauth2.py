from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from redis_client import redis_client
from .config import SECRET_KEY, ALGORITHM

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("id")
        role = payload.get("role")

        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")

        stored_token = redis_client.get(f"user_token:{user_id}")
        if stored_token != token:
            raise HTTPException(status_code=401, detail="Session expired")

        return {"username": username, "id": user_id, "role": role}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
