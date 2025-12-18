import json
import uuid

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import HTMLResponse

from models import Users
from redis_client import redis_client
from oauth_config import oauth
from .config import REDIRECT_URI

from .hashing import Hash
from .jwt_utils import create_access_token, decode_access_token
from .email_service import EmailService
import random

from .oauth2 import get_current_user


class AuthService:

    # ------------------------ CREATE USER ------------------------
    @staticmethod
    async def create_user(req, db: Session):
        existing = db.query(Users).filter(Users.email == req.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

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

        # 🔐 Generate OTP
        otp = str(random.randint(100000, 999999))

        # 🧠 Store OTP in Redis (5 minutes)
        redis_client.set(
            f"email_otp:{user.email}",
            otp,
            ex=300
        )

        EmailService.send_otp(user.email, otp)

        return {
            "message": "OTP sent to email",
            "email": user.email
        }

    # ------------------------ LOGIN (USERNAME + PASSWORD) ------------------------
    @staticmethod
    async def login(form_data: OAuth2PasswordRequestForm, db: Session):
        user = db.query(Users).filter(Users.email == form_data.username).first()

        if not user or not user.hashed_password:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not Hash.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Please verify your email first.")

        if not user.username:
            raise HTTPException(
                status_code=403,
                detail="Complete signup step 2 first"
            )

        token = create_access_token(
            email=user.email,  # 👈 use email in JWT
            user_id=user.id,
            expires_delta=timedelta(minutes=30)
        )

        # session_token = str(uuid.uuid4())
        # redis_client.set(f"user_token:{session_token}", token, ex=60)

        return {
            "access_token": token,  # JWT
            "token_type": "bearer"
        }

    # ------------------------ VERIFY OTP ------------------------
    @staticmethod
    async def verify_otp(email: str, otp: str, db: Session):

        stored_otp = redis_client.get(f"email_otp:{email}")

        if not stored_otp:
            raise HTTPException(status_code=400, detail="OTP expired or invalid")

        if stored_otp != otp:
            raise HTTPException(status_code=400, detail="Incorrect OTP")

        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_verified = True
        db.commit()

        redis_client.delete(f"email_otp:{email}")

        access_token = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=120)
        )


        return {
            "token": access_token,
            "token_type": "bearer",
            "expires_in": 7200
        }

    # ------------------------ GOOGLE LOGIN ------------------------
    @staticmethod
    async def google_login(request: Request):
        google = oauth.create_client("google")
        return await google.authorize_redirect(request, REDIRECT_URI)

    # ------------------------ GITHUB LOGIN ------------------------
    @staticmethod
    async def github_login(request: Request):
        github = oauth.create_client("github")
        return await github.authorize_redirect(request, REDIRECT_URI)

    # ------------------------ FIXED OAUTH CALLBACK ------------------------
    @staticmethod
    async def oauth_callback(request: Request, db: Session):

        # -------- Detect provider --------
        is_google = "google" in str(request.url)

        email = None
        full_name = None
        picture_url = None

        if is_google:
            provider = oauth.create_client("google")
            token = await provider.authorize_access_token(request)
            user_info = token.get("userinfo")

            email = user_info["email"]
            full_name = user_info.get("name", "")
            picture_url = user_info.get("picture")

        else:
            provider = oauth.create_client("github")
            token = await provider.authorize_access_token(request)

            github_user = await provider.get("user", token=token)
            github_email = await provider.get("user/emails", token=token)

            email = github_email.json()[0]["email"]
            full_name = github_user.json().get("name") or github_user.json().get("login")
            picture_url = github_user.json().get("avatar_url")

        # -------- Split first & last name --------
        first_name = ""
        last_name = ""

        if full_name:
            name_parts = full_name.strip().split()
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # -------- Create or update user --------
        user = db.query(Users).filter(Users.email == email).first()

        if not user:
            user = Users(
                email=email,
                username=None,  # ✅ username is NULL
                first_name=first_name,
                last_name=last_name,
                hashed_password=None,  # OAuth users don’t have passwords
                is_active=True,
                is_verified=True,
                profile_image=picture_url
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            updated = False
            if picture_url and user.profile_image != picture_url:
                user.profile_image = picture_url
                updated = True
            if not user.first_name:
                user.first_name = first_name
                user.last_name = last_name
                updated = True
            if updated:
                db.commit()

        # -------- Create JWT --------
        jwt_token = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=30)
        )

        session_key = str(uuid.uuid4())

        user_dict = {
            "id": user.id,
            "name": user.first_name,
            "email": user.email,
            "photoUrl": user.profile_image
        }

        redis_client.set(f"user_token:{session_key}", jwt_token, ex=120)
        redis_client.set(f"user_data:{session_key}", json.dumps(user_dict), ex=120)

        # -------- Redirect to Flutter deep link --------
        deep_link = f"hackmates://oauth/callback?key={session_key}"

        return HTMLResponse(
            content=f"""
            <html>
                <body>
                    <script>
                        window.location.href = "{deep_link}";
                    </script>
                    <p>Redirecting back to app...</p>
                </body>
            </html>
            """
        )

    # ------------------------ LOGOUT ------------------------
    @staticmethod
    async def logout(current_user):
        session_token = current_user["session_token"]
        redis_client.delete(f"user_token:{session_token}")
        return {"message": "Logged out successfully"}

    @staticmethod
    async def resend_otp(email: str, db: Session):

        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_verified:
            raise HTTPException(status_code=400, detail="Email already verified")

        otp = str(random.randint(100000, 999999))

        redis_client.set(
            f"email_otp:{email}",
            otp,
            ex=300
        )

        EmailService.send_otp(email, otp)

        return {"message": "OTP resent successfully"}



    @staticmethod
    async def forgot_password(email: str, db: Session):
        user = db.query(Users).filter(Users.email == email).first()

        # Security best practice: don't reveal if email exists
        if not user:
            return {"message": "If the email exists, a reset link has been sent"}

        reset_token = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=15)
        )

        reset_link = f"https://uncookable-annelle-combatable.ngrok-free.dev/auth/reset-password?token={reset_token}"

        EmailService.send_password_reset(user.email, reset_link)

        return {"message": "Password reset link sent"}

    @staticmethod
    async def reset_password(token: str, new_password: str, db: Session):
        try:
            payload = decode_access_token(token)
            user_id = payload["user_id"]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.hashed_password = Hash.hash(new_password)
        db.commit()

        redis_client.delete(f"email_otp:{user.email}")

        return {"message": "Password updated successfully"}




