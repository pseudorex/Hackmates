from fastapi import (
    APIRouter, Depends, HTTPException, Request,
    Form, File, UploadFile
)
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from fastapi.security import OAuth2PasswordRequestForm
import json

from starlette.responses import HTMLResponse

from redis_client import redis_client
from database import SessionLocal
from models import Users, Skills
from cloudinary.uploader import upload

from .schemas import (
    CreateUserRequest,
    Token,
    VerifyOtpRequest,
    CompleteProfileRequest
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
async def login_route(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    return await AuthService.login(form_data, db)


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

# ---------------- Complete Profile ----------------
@router.post("/complete-profile")
async def complete_profile(
    bio: str = Form(None),
    interests: str = Form(None),              # JSON string: ["python","flutter"]
    profilePhoto: UploadFile | None = File(None),

    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    print("\n===== COMPLETE PROFILE HIT =====")

    print("bio:", bio)
    print("skills (raw):", interests)

    # 🔹 Parse skills
    try:
        skills_list = json.loads(interests) if interests else []
    except Exception:
        raise HTTPException(status_code=400, detail="Skills must be a JSON array")

    # 🔹 Validate
    profile = CompleteProfileRequest(
        bio=bio,
        skills=skills_list
    )

    # 🔹 Load user
    user = db.query(Users).filter(Users.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔹 Save bio
    user.bio = profile.bio

    # 🔹 Save skills
    skill_objects = []
    for skill_name in profile.skills:
        skill = db.query(Skills).filter(Skills.name == skill_name).first()
        if not skill:
            skill = Skills(name=skill_name)
            db.add(skill)
            db.flush()
        skill_objects.append(skill)

    user.skills = skill_objects

    # 🔹 Upload image
    if profilePhoto:
        result = upload(profilePhoto.file)
        user.profile_image = result.get("secure_url")
        print("Image URL:", user.profile_image)
    else:
        print("No image uploaded")

    db.commit()
    db.refresh(user)

    return {
        "message": "Profile completed successfully",
        "bio": user.bio,
        "skills": [s.name for s in user.skills],
        "profile_image": user.profile_image,
    }


@router.post("/forgot-password")
async def forgot_password(data: dict, db: db_dependency):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    return await AuthService.forgot_password(email=email, db=db)


# @router.get("/reset-password", response_class=HTMLResponse)
# async def reset_password_page(token: str):
#     return f"""
#     <html>
#         <body>
#             <h2>Reset Password</h2>
#             <form method="POST" action="/auth/reset-password">
#                 <input type="hidden" name="token" value="{token}" />
#
#                 <label>New Password</label><br/>
#                 <input type="password" name="password" required /><br/><br/>
#
#                 <label>Confirm Password</label><br/>
#                 <input type="password" name="confirm_password" required /><br/><br/>
#
#                 <button type="submit">Change Password</button>
#             </form>
#         </body>
#     </html>
#     """

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

