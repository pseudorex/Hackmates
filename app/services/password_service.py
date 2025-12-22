from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta

from app.models.users import Users
from app.core.hashing import Hash
from app.core.jwt_utils import create_access_token, decode_access_token
from app.services.email_service import EmailService


class PasswordService:

    @staticmethod
    async def forgot_password(email: str, db: Session):
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            return {"message": "If email exists, reset link sent"}

        token = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=15)
        )

        EmailService.send_password_reset(user.email, token)
        return {"message": "Reset link sent"}

    @staticmethod
    async def reset_password(token: str, new_password: str, db: Session):
        payload = decode_access_token(token)
        user = db.query(Users).filter(Users.id == payload["user_id"]).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.hashed_password = Hash.hash(new_password)
        db.commit()

        return {"message": "Password updated"}
