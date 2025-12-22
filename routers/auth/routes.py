from fastapi import (
    APIRouter, Depends, HTTPException, Request,
    Form, File, UploadFile
)
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from fastapi.security import OAuth2PasswordRequestForm
from database import SessionLocal

from .schemas import (
    CreateUserRequest,
    Token,
    VerifyOtpRequest,
)
from .oauth2 import get_current_user
from .service import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/register", status_code=201)
async def create_user_route(db: db_dependency, req: CreateUserRequest):
    return await AuthService.create_user(req, db)


@router.post("/login", response_model=Token)
async def login_route(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    return await AuthService.login(form_data, db)


@router.get("/google")
async def google_login(request: Request):
    return await AuthService.google_login(request)


@router.get("/github")
async def github_login(request: Request):
    return await AuthService.github_login(request)


@router.api_route("/callback", methods=["GET", "POST"])
async def callback_route(request: Request, db: db_dependency):
    return await AuthService.oauth_callback(request, db)


@router.post("/logout")
async def logout_route(current_user=Depends(get_current_user)):
    return await AuthService.logout(current_user)


# ---------------- GET JWT AFTER OAUTH ----------------
@router.get("/getJwt")
async def get_oauth_jwt(key: str):
    return await AuthService.get_oauth_jwt(key)


@router.post("/resend-otp")
async def resend_otp(data: dict, db: db_dependency):
    return await AuthService.resend_otp(
        email=data["email"],
        db=db
    )


@router.post("/verify-otp")
async def verify_otp(data: VerifyOtpRequest, db: db_dependency):
    return await AuthService.verify_otp(
        email=data.email,
        otp=data.otp,
        db=db
    )


# ---------------- COMPLETE PROFILE ----------------
@router.post("/complete-profile")
async def complete_profile(
    bio: Optional[str] = Form(None),
    interests: Optional[str] = Form(None),
    profilePhoto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await AuthService.complete_profile(
        bio, interests, profilePhoto, db, current_user
    )


# ---------------- FORGOT / RESET PASSWORD ----------------
@router.post("/forgot-password")
async def forgot_password(data: dict, db: db_dependency):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    return await AuthService.forgot_password(email=email, db=db)


@router.post("/reset-password")
async def reset_password_api(
    data: dict,
    db: Session = Depends(get_db)
):
    token = data.get("token")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not token or not password or not confirm_password:
        raise HTTPException(status_code=400, detail="All fields are required")

    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    await AuthService.reset_password(token, password, db)

    return {"message": "Password reset successful"}
