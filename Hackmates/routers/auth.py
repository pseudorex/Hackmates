# auth.py
import os
from datetime import timedelta, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv

from database import SessionLocal
from models import Users
from oauth_config import oauth

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------- Schemas ----------------
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ---------------- DB Dependency ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# ---------------- Auth Helpers ----------------
def authenticate_user(username: str, password: str, db: Session):
    user = db.query(Users).filter(Users.username == username).first()
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    payload = {
        "sub": username,
        "id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("id")
        role = payload.get("role")
        if not username or not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------- Normal Auth ----------------
@router.post("/", status_code=201)
async def create_user(db: db_dependency, user_req: CreateUserRequest):
    user = Users(
        email=user_req.email,
        username=user_req.username,
        first_name=user_req.first_name,
        last_name=user_req.last_name,
        role=user_req.role,
        hashed_password=bcrypt_context.hash(user_req.password),
        is_active=True,
        phone_number=user_req.phone_number
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "User created", "user_id": user.id}

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(
        user.username, user.id, user.role, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}

# ---------------- OAuth Routes ----------------
@router.get("/google")
async def google_login(request: Request):
    google = oauth.create_client("google")
    redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
    return await google.authorize_redirect(request, redirect_uri)

@router.get("/github")
async def github_login(request: Request):
    github = oauth.create_client("github")
    redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
    return await github.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def auth_callback(request: Request, db: db_dependency):
    url = str(request.url)

    if "google" in url:
        client = oauth.create_client("google")
        token = await client.authorize_access_token(request)
        user_info = token.get("userinfo")
        email = user_info["email"]
        name = user_info["name"]
    else:  # GitHub
        client = oauth.create_client("github")
        token = await client.authorize_access_token(request)
        user_data = await client.get("user", token=token)
        emails_data = await client.get("user/emails", token=token)
        emails = emails_data.json()

        if emails:
            primary_email = next(
                (e['email'] for e in emails if e.get('primary') and e.get('verified')),
                emails[0].get("email")
            )
        else:
            raise HTTPException(status_code=400, detail="No email found in GitHub account")

        email = primary_email
        name = user_data.json()["login"]

    # Check if user exists or create
    user = db.query(Users).filter(Users.email == email).first()
    if not user:
        user = Users(
            email=email,
            username=name,
            first_name=name,
            last_name="",
            role="user",
            hashed_password=bcrypt_context.hash("oauthuser"),
            is_active=True,
            phone_number=""
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Issue JWT
    jwt_token = create_access_token(user.username, user.id, user.role, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": jwt_token, "token_type": "bearer"}
