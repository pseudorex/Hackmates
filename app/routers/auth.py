from fastapi import (
    APIRouter, Depends, Request,
    Form, File, UploadFile, HTTPException
)
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.models import Users
from app.schemas.auth_schema import CreateUserRequest, VerifyOtpRequest
from app.schemas.token_schema import Token

from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService
from app.services.password_service import PasswordService
from app.services.profile_service import ProfileService
from app.services.session_service import SessionService

from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------- REGISTER ----------------
@router.post("/register", status_code=201)
async def register(
    payload: CreateUserRequest,
    db: Session = Depends(get_db)
):
    return await AuthService.create_user(payload, db)


# ---------------- LOGIN ----------------
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    return await AuthService.login(form_data, db)


# ---------------- OTP ----------------
@router.post("/verify-otp")
async def verify_otp(
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db)
):
    return await AuthService.verify_otp(
        email=payload.email,
        otp=payload.otp,
        db=db
    )


@router.post("/resend-otp")
async def resend_otp(
    data: dict,
    db: Session = Depends(get_db)
):
    return await AuthService.resend_otp(
        email=data["email"],
        db=db
    )


# ---------------- OAUTH ----------------
@router.get("/google")
async def google_login(request: Request):
    return await OAuthService.login("google", request)


@router.get("/github")
async def github_login(request: Request):
    return await OAuthService.login("github", request)


@router.api_route("/callback", methods=["GET", "POST"])
async def oauth_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    return await OAuthService.callback(request, db)


@router.get("/get-jwt")
async def get_oauth_jwt(key: str):
    return SessionService.get_oauth_session(key)


# ---------------- PROFILE ----------------
@router.post("/complete-profile")
async def complete_profile(
    bio: str | None = Form(None),
    interests: str | None = Form(None),
    profilePhoto: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ProfileService.complete_profile(
        bio, interests, profilePhoto, db, current_user
    )


# ---------------- PASSWORD ----------------
@router.post("/forgot-password")
async def forgot_password(
    data: dict,
    db: Session = Depends(get_db)
):
    return await PasswordService.forgot_password(
        email=data["email"],
        db=db
    )


@router.post("/reset-password")
async def reset_password(
    data: dict,
    db: Session = Depends(get_db)
):
    if data["password"] != data["confirm_password"]:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    return await PasswordService.reset_password(
        token=data["token"],
        new_password=data["password"],
        db=db
    )

@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = db.query(Users).filter(
        Users.id == current_user["user_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user": {
            "id": user.id,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "email": user.email,
            "photoUrl": user.profile_image,
            "bio": user.bio,
            "interests": [skill.name for skill in user.skills],
            "isVerified": user.is_verified, # or True if verified by OTP
        }
    }