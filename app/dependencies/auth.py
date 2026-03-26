from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status, Depends
from app.core.jwt_utils import decode_access_token

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = decode_access_token(token)

        email = payload.get("email")
        user_id = payload.get("user_id")

        if not email or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        return {
            "email": email,
            "user_id": user_id
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
