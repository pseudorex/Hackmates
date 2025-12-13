import json
import uuid
import cloudinary
import cloudinary.uploader

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from models import Users
from redis_client import redis_client
from oauth_config import oauth

from .hashing import Hash
from .jwt_utils import create_access_token
from .email_service import EmailService
from .config import REDIRECT_URI, SECRET_KEY, ALGORITHM
from jose import jwt



class AuthService:

    # ------------------------ CREATE USER ------------------------
    @staticmethod
    async def create_user(req, db: Session):
        existing = db.query(Users).filter(Users.email == req.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = Users(
            email=req.email,
            username="Hello",
            first_name=req.firstName,
            last_name=req.lastName,
            hashed_password=Hash.hash(req.password),
            is_active=True,
            is_verified=False,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Email verification
        EmailService.send_verification(user)

        return {"message": "User created successfully! Please verify your email."}

    # ------------------------ LOGIN (USERNAME + PASSWORD) ------------------------
    @staticmethod
    async def login(form_data: OAuth2PasswordRequestForm, db: Session):
        user = db.query(Users).filter(Users.username == form_data.username).first()

        if not user or not Hash.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Please verify your email first.")

        token = create_access_token(
            username=user.username,
            user_id=user.id,
            expires_delta=timedelta(minutes=30)
        )

        session_token = str(uuid.uuid4())
        redis_client.set(f"user_token:{session_token}", token, ex=60)

        return {"access_token": session_token, "token_type": "redis"}

    # ------------------------ VERIFY EMAIL ------------------------
    @staticmethod
    async def verify_email(token: str, db: Session):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")

            if not email:
                raise HTTPException(status_code=400, detail="Invalid token")

            user = db.query(Users).filter(Users.email == email).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # 🔐 Already verified guard
            if user.is_verified:
                deep_link = "hackmates://verified?already=true"
                return HTMLResponse(
                    f"""
                    <html>
                      <head>
                        <meta http-equiv="refresh" content="0;url={deep_link}">
                      </head>
                      <body>
                        <p>Email already verified. Redirecting…</p>
                      </body>
                    </html>
                    """
                )

            # ✅ Mark verified
            user.is_verified = True
            db.commit()

            # Create JWT
            access_token = create_access_token(
                username=user.username,
                user_id=user.id,
                expires_delta=timedelta(minutes=30)
            )

            # Store in Redis
            session_token = str(uuid.uuid4())
            redis_client.set(f"user_token:{session_token}", access_token, ex=300)

            # 🔥 Redirect to Flutter Signup Step-2
            deep_link = f"hackmates://verified?token={session_token}"

            return HTMLResponse(
                f"""
                <html>
                  <head>
                    <meta http-equiv="refresh" content="0;url={deep_link}">
                  </head>
                  <body>
                    <p>Email verified. Redirecting back to app…</p>
                  </body>
                </html>
                """
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=400, detail="Verification link expired")
        except jwt.JWTError:
            raise HTTPException(status_code=400, detail="Invalid token")

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

        if is_google:
            provider = oauth.create_client("google")
            token = await provider.authorize_access_token(request)
            user_info = token.get("userinfo")

            email = user_info["email"]
            name = user_info["name"]
            picture_url = user_info.get("picture")

        else:
            provider = oauth.create_client("github")
            token = await provider.authorize_access_token(request)

            github_user = await provider.get("user", token=token)
            github_email = await provider.get("user/emails", token=token)

            email = github_email.json()[0]["email"]
            name = github_user.json()["login"]
            picture_url = github_user.json().get("avatar_url")

        # -------- Cloudinary upload --------
        cloud_image_url = None
        if picture_url:
            try:
                upload = cloudinary.uploader.upload(picture_url)
                cloud_image_url = upload["secure_url"]
            except:
                pass

        # -------- Create or update user --------
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            user = Users(
                email=email,
                username=name,
                first_name=name,
                last_name="",
                hashed_password=None,
                is_active=True,
                is_verified=True,
                profile_image=cloud_image_url
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            if cloud_image_url and user.profile_image != cloud_image_url:
                user.profile_image = cloud_image_url
                db.commit()

        # -------- Create JWT --------
        jwt_token = create_access_token(
            username=user.username,
            user_id=user.id,
            expires_delta=timedelta(minutes=30)
        )

        session_key = str(uuid.uuid4())

        user_dict = {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "photoUrl": user.profile_image
        }

        redis_client.set(f"user_token:{session_key}", jwt_token, ex=120)
        redis_client.set(f"user_data:{session_key}", json.dumps(user_dict), ex=120)

        # -------- Redirect to Flutter deep link --------
        deep_link = f"hackmates://oauth/callback?key={session_key}"

        html_page = f"""
            <html>
                <body>
                    <script>
                        // This will redirect back to Flutter app immediately
                        window.location.href = "{deep_link}";
                    </script>
                    <p>Redirecting back to app...</p>
                </body>
            </html>
            """

        return HTMLResponse(content=html_page)
    # ------------------------ LOGOUT ------------------------
    @staticmethod
    async def logout(current_user):
        session_token = current_user["session_token"]
        redis_client.delete(f"user_token:{session_token}")
        return {"message": "Logged out successfully"}
