from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi import Request
from oauth_config import oauth
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from jose import jwt
import os
from .email_utils import send_verification_email

# --------------------------- SETUP ---------------------------
router = APIRouter(prefix='/auth', tags=['auth'])

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
REDIRECT_URI = os.getenv("REDIRECT_URI")

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

# --------------------------- SCHEMAS ---------------------------
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

# --------------------------- DEPENDENCIES ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# --------------------------- HELPERS ---------------------------
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def create_email_verification_token(email: str, expires_hours: int = 24):
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# --------------------------- VERIFY CURRENT USER ---------------------------
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')

        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user.')

        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')

# --------------------------- CREATE USER ---------------------------
@router.post("/", status_code=201)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    # Check if email already exists
    existing_user = db.query(Users).filter(Users.email == create_user_request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True,
        is_verified=False,
        phone_number=create_user_request.phone_number
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Send verification email
    token = create_email_verification_token(user.email)
    send_verification_email(user.email, token)

    return {"message": "✅ User created! Please check your email to verify your account."}

# --------------------------- LOGIN ---------------------------
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')

    # Check if verified
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=30))
    return {'access_token': token, 'token_type': 'bearer'}

# --------------------------- EMAIL VERIFICATION ---------------------------
@router.get("/verify-email")
async def verify_email(token: str, db: db_dependency):
    try:
        # Decode verification token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")

        # Find user
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Mark as verified
        user.is_verified = True
        db.commit()
        db.refresh(user)

        # ✅ Create JWT for the verified user
        access_token = create_access_token(
            username=user.username,
            user_id=user.id,
            role=user.role,
            expires_delta=timedelta(minutes=30)
        )

        return {
            "message": "✅ Email verified successfully!",
            "access_token": access_token,
            "token_type": "bearer"
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Verification link expired.")
    except jwt.JWTError:
        raise HTTPException(status_code=400, detail="Invalid token.")



# --------------------------- OAUTH ROUTES ---------------------------
@router.get("/google")
async def google_login(request: Request):
    google = oauth.create_client("google")
    return await google.authorize_redirect(request, REDIRECT_URI)

@router.get("/github")
async def github_login(request: Request):
    github = oauth.create_client("github")
    return await github.authorize_redirect(request, REDIRECT_URI)

@router.get("/callback")
async def auth_callback(request: Request, db: db_dependency):
    if "google" in str(request.url):
        google = oauth.create_client("google")
        token = await google.authorize_access_token(request)
        user_info = token.get("userinfo")
        email = user_info["email"]
        name = user_info["name"]
    else:
        github = oauth.create_client("github")
        token = await github.authorize_access_token(request)
        user_data = await github.get("user", token=token)
        email_data = await github.get("user/emails", token=token)
        email = email_data.json()[0]["email"]
        name = user_data.json()["login"]

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
            is_verified=True,
            phone_number=""
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token(user.username, user.id, user.role, timedelta(minutes=30))
    return {'access_token': jwt_token, 'token_type': 'bearer'}
