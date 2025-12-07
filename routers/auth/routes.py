from fastapi import APIRouter, Depends, HTTPException, Request, status
from .schemas import CreateUserRequest, Token
from .oauth2 import get_current_user
from .service import AuthService
from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/", status_code=201)
async def create_user_route(db: db_dependency, req: CreateUserRequest):
    return await AuthService.create_user(req, db)

@router.post("/token", response_model=Token)
async def login_route(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                      db: db_dependency):
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

@router.get("/callback")
async def callback_route(request: Request, db: db_dependency):
    return await AuthService.oauth_callback(request, db)

@router.post("/logout")
async def logout_route(current_user=Depends(get_current_user)):
    return await AuthService.logout(current_user)
