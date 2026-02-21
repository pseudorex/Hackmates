import random
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.models.users import Users
from app.redis_client import redis_client
from app.core.hashing import Hash
from app.core.jwt_utils import create_access_token, create_refresh_token, verify_token
from app.services.email_service import EmailService


class AuthService:

    @staticmethod
    async def create_user(req, db: Session):
        existing = db.query(Users).filter(Users.email == req.email).first()

        # Case 1: Already verified → hard stop
        if existing and existing.is_verified:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        # Case 2: New user → create
        if not existing:
            user = Users(
                email=req.email,
                username=None,
                first_name=req.firstName,
                last_name=req.lastName,
                hashed_password=Hash.hash(req.password),
                is_active=True,
                is_verified=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Case 3: Exists but NOT verified
            user = existing

        # Send / resend OTP
        otp = str(random.randint(100000, 999999))
        redis_client.set(f"email_otp:{user.email}", otp, ex=300)
        EmailService.send_otp(user.email, otp)

        return {
            "message": (
                "OTP sent to email"
                if not existing
                else "Email already registered but not verified. OTP resent."
            ),
            "email": user.email,
            "verification_pending": True
        }

    @staticmethod
    async def login(form_data: OAuth2PasswordRequestForm, db: Session):
        user = db.query(Users).filter(Users.email == form_data.username).first()

        if not user or not user.hashed_password:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not Hash.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Email not verified")

        access_token = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=1)
        )


        refresh_token = create_refresh_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(days=7)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    async def verify_otp(email: str, otp: str, db: Session):
        stored_otp = redis_client.get(f"email_otp:{email}")

        if not stored_otp:
            raise HTTPException(status_code=400, detail="OTP expired or not found")

        # 🚫 NO decode here
        if stored_otp != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_verified = True
        db.commit()

        redis_client.delete(f"email_otp:{email}")
        redis_client.delete(f"email_otp_resend:{email}")

        token = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=120)
        )

        refresh_token = create_refresh_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(days=7)
        )

        return {
            "access_token": token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    async def resend_otp(email: str, db: Session):
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_verified:
            raise HTTPException(status_code=400, detail="Email already verified")

        # Optional rate limit (30s)
        resend_key = f"email_otp_resend:{email}"
        if redis_client.get(resend_key):
            raise HTTPException(
                status_code=429,
                detail="Please wait before requesting another OTP"
            )

        otp = str(random.randint(100000, 999999))

        redis_client.set(f"email_otp:{email}", otp, ex=300)
        redis_client.set(resend_key, "1", ex=30)

        EmailService.send_otp(email, otp)

        return {"message": "OTP resent successfully"}

    @staticmethod
    async def refresh_access_token(refresh_token: str, db: Session):

        payload = verify_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("user_id")

        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        new_access_token = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=30)
        )

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,  # rotation can be added later
            "token_type": "bearer"
        }

