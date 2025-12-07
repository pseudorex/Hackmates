from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from models import Users
from redis_client import redis_client
from oauth_config import oauth

from .hashing import Hash
from .jwt_utils import create_access_token, create_email_verification_token
from .email_service import EmailService
from .config import REDIRECT_URI, SECRET_KEY, ALGORITHM


class AuthService:

    # ------------------------ CREATE USER ------------------------
    @staticmethod
    async def create_user(req, db: Session):
        # Check if email already registered
        existing = db.query(Users).filter(Users.email == req.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = Users(
            email=req.email,
            username=req.username,
            first_name=req.first_name,
            last_name=req.last_name,
            role=req.role,
            hashed_password=Hash.hash(req.password),
            is_active=True,
            is_verified=False,
            phone_number=req.phone_number
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Send verification email
        EmailService.send_verification(user)

        return {
            "message": "User created successfully! Please verify your email."
        }

    # ------------------------ LOGIN ------------------------
    @staticmethod
    async def login(form_data: OAuth2PasswordRequestForm, db: Session):
        user = db.query(Users).filter(Users.username == form_data.username).first()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not Hash.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Please verify your email first.")

        # Create access token
        token = create_access_token(
            username=user.username,
            user_id=user.id,
            role=user.role,
            expires_delta=timedelta(minutes=30)
        )

        # Store token in Redis (for session control)
        redis_client.set(f"user_token:{user.id}", token, ex=1800)

        return {"access_token": token, "token_type": "bearer"}

    # ------------------------ VERIFY EMAIL ------------------------
    @staticmethod
    async def verify_email(token: str, db: Session):
        from jose import jwt

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")

            if not email:
                raise HTTPException(status_code=400, detail="Invalid token")

            user = db.query(Users).filter(Users.email == email).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Mark user verified
            user.is_verified = True
            db.commit()

            # Create access token after verification
            access_token = create_access_token(
                username=user.username,
                user_id=user.id,
                role=user.role,
                expires_delta=timedelta(minutes=30)
            )

            redis_client.set(f"user_token:{user.id}", access_token, ex=1800)

            return {
                "message": "Email verified!",
                "access_token": access_token,
                "token_type": "bearer"
            }

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

    # ------------------------ OAUTH CALLBACK ------------------------
    @staticmethod
    async def oauth_callback(request: Request, db: Session):

        # ------------------ Google Auth ------------------
        if "google" in str(request.url):
            google = oauth.create_client("google")
            token = await google.authorize_access_token(request)
            user_info = token.get("userinfo")

            email = user_info["email"]
            name = user_info["name"]

        # ------------------ GitHub Auth ------------------
        else:
            github = oauth.create_client("github")
            token = await github.authorize_access_token(request)

            github_user = await github.get("user", token=token)
            github_email = await github.get("user/emails", token=token)

            email = github_email.json()[0]["email"]
            name = github_user.json()["login"]

        # Find or create user
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            user = Users(
                email=email,
                username=name,
                first_name=name,
                last_name="",
                role="user",
                hashed_password=Hash.hash("oauthuser"),
                is_active=True,
                is_verified=True,
                phone_number=""
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Generate JWT
        jwt_token = create_access_token(
            username=user.username,
            user_id=user.id,
            role=user.role,
            expires_delta=timedelta(minutes=30)
        )

        redis_client.set(f"user_token:{user.id}", jwt_token, ex=1800)

        return {
            "access_token": jwt_token,
            "token_type": "bearer"
        }

    # ------------------------ LOGOUT ------------------------
    @staticmethod
    async def logout(current_user):
        user_id = current_user["id"]
        redis_client.delete(f"user_token:{user_id}")

        return {"message": "Logged out successfully"}
