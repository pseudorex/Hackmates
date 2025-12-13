from fastapi import APIRouter, Depends, HTTPException, Request

from models import Users
from redis_client import redis_client
from .email_service import EmailService
from .schemas import CreateUserRequest, Token
from .oauth2 import get_current_user
from .service import AuthService
from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
import json

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
async def login_route(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    return await AuthService.login(form_data, db)

@router.get("/verify-email")
async def verify_email_route(token: str, db: db_dependency):
    return await AuthService.verify_email(token, db)

@router.get("/google")
async def google_login(request: Request):
    return await AuthService.google_login(request)

@router.get("/github")
async def github_login(request: Request):
    return await AuthService.github_login(request)

# IMPORTANT FIX: allow POST + GET
@router.api_route("/callback", methods=["GET", "POST"])
async def callback_route(request: Request, db: db_dependency):
    return await AuthService.oauth_callback(request, db)

@router.post("/logout")
async def logout_route(current_user=Depends(get_current_user)):
    return await AuthService.logout(current_user)

# ------------------------ GET JWT AFTER OAUTH ------------------------
@router.get("/getJwt")
async def get_oauth_jwt(key: str):
    jwt_token = redis_client.get(f"user_token:{key}")
    user_data = redis_client.get(f"user_data:{key}")

    if not jwt_token or not user_data:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth key")

    # Redis already returns string
    jwt_token = jwt_token
    user_data = json.loads(user_data)

    # Clean up redis
    redis_client.delete(f"user_token:{key}")
    redis_client.delete(f"user_data:{key}")

    return {
        "token": jwt_token,
        "tokenType": "Bearer",
        "expiresIn": 3600,
        "user": user_data
    }

@router.post("/resend-verification")
async def resend_verification(email: dict, db: db_dependency):
    user = db.query(Users).filter(Users.email == email["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    EmailService.send_verification(user)
    return {"message": "Verification email resent"}

