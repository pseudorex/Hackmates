import json
import uuid
import random
from typing import Optional

from fastapi import HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import HTMLResponse

from models import Users, Skills
from redis_client import redis_client
from oauth_config import oauth
from .config import REDIRECT_URI

from .hashing import Hash
from .jwt_utils import create_access_token, decode_access_token
from .email_service import EmailService
from .schemas import CompleteProfileRequest
from cloudinary.uploader import upload


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

    # ------------------------ LOGIN ------------------------
    @staticmethod
    async def login(form_data: OAuth2PasswordRequestForm, db: Session):
        user = db.query(Users).filter(Users.email == form_data.username).first()

        if not user or not user.hashed_password:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not Hash.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Please verify your email first")

        token = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=30)
        )

        return {
            "access_token": token,
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

        token = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=120)
        )

        return {
            "token": token,
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

    # ------------------------ OAUTH CALLBACK ------------------------
    @staticmethod
    async def oauth_callback(request: Request, db: Session):
        is_google = "google" in str(request.url)

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

        parts = full_name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            user = Users(
                email=email,
                username=None,
                first_name=first_name,
                last_name=last_name,
                hashed_password=None,
                is_active=True,
                is_verified=True,
                profile_image=picture_url
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        jwt_token = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=30)
        )

        session_key = str(uuid.uuid4())

        redis_client.set(f"user_token:{session_key}", jwt_token, ex=120)
        redis_client.set(
            f"user_data:{session_key}",
            json.dumps({
                "id": user.id,
                "name": user.first_name,
                "email": user.email,
                "photoUrl": user.profile_image
            }),
            ex=120
        )

        deep_link = f"hackmates://oauth/callback?key={session_key}"

        return HTMLResponse(
            f"""
            <html>
                <body>
                    <script>
                        window.location.href = "{deep_link}";
                    </script>
                </body>
            </html>
            """
        )

    # ------------------------ RESEND OTP ------------------------
    @staticmethod
    async def resend_otp(email: str, db: Session):
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        otp = str(random.randint(100000, 999999))
        redis_client.set(f"email_otp:{email}", otp, ex=300)

        EmailService.send_otp(email, otp)
        return {"message": "OTP resent successfully"}

    # ------------------------ FORGOT PASSWORD ------------------------
    @staticmethod
    async def forgot_password(email: str, db: Session):
        user = db.query(Users).filter(Users.email == email).first()
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

    # ------------------------ RESET PASSWORD ------------------------
    @staticmethod
    async def reset_password(token: str, new_password: str, db: Session):
        payload = decode_access_token(token)
        user_id = payload["user_id"]

        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.hashed_password = Hash.hash(new_password)
        db.commit()

        return {"message": "Password updated successfully"}

    @staticmethod
    async def get_oauth_jwt(key: str):
        jwt_token = redis_client.get(f"user_token:{key}")
        user_data = redis_client.get(f"user_data:{key}")

        if not jwt_token or not user_data:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth key")

        user_data = json.loads(user_data)

        redis_client.delete(f"user_token:{key}")
        redis_client.delete(f"user_data:{key}")

        return {
            "token": jwt_token,
            "tokenType": "Bearer",
            "expiresIn": 3600,
            "user": user_data
        }

    @staticmethod
    async def complete_profile(
            bio: Optional[str],
            interests: Optional[str],
            profilePhoto: Optional[UploadFile],
            db: Session,
            current_user: dict,
    ):

        # ---- Parse skills safely ----
        try:
            skills_list = json.loads(interests) if interests else []
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid interests format"
            )

        profile = CompleteProfileRequest(
            bio=bio,
            skills=skills_list
        )

        # ---- Fetch user ----
        user = db.query(Users).filter(
            Users.id == current_user["user_id"]
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # ---- Update bio ----
        user.bio = profile.bio

        # ---- Handle skills ----
        skill_objects = []
        for skill_name in profile.skills:
            skill = db.query(Skills).filter(
                Skills.name == skill_name.strip().lower()
            ).first()

            if not skill:
                skill = Skills(name=skill_name)
                db.add(skill)
                db.flush()

            skill_objects.append(skill)

        user.skills = skill_objects

        # ---- Upload profile photo ----
        if profilePhoto:
            try:
                result = upload(profilePhoto.file)
                user.profile_image = result.get("secure_url")
            except Exception:
                raise HTTPException(status_code=500, detail="Image upload failed")

        db.commit()
        db.refresh(user)

        return {
            "message": "Profile completed successfully",
            "bio": user.bio,
            "skills": [s.name for s in user.skills],
            "profile_image": user.profile_image,
        }

