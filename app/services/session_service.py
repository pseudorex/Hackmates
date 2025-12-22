import json
from fastapi import HTTPException
from app.redis_client import redis_client


class SessionService:

    @staticmethod
    def store_oauth_session(key: str, jwt_token: str, user_data: dict):
        redis_client.set(
            f"user_token:{key}",
            jwt_token,
            ex=120
        )
        redis_client.set(
            f"user_data:{key}",
            json.dumps(user_data),
            ex=120
        )

    @staticmethod
    def get_oauth_session(key: str):
        jwt_token = redis_client.get(f"user_token:{key}")
        user_data = redis_client.get(f"user_data:{key}")

        if not jwt_token or not user_data:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired OAuth key"
            )

        redis_client.delete(f"user_token:{key}")
        redis_client.delete(f"user_data:{key}")

        return {
            "token": jwt_token,
            "tokenType": "Bearer",
            "expiresIn": 3600,
            "user": json.loads(user_data)
        }
