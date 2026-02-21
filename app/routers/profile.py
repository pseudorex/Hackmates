from typing import Optional

from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session

from app.services.profile_service import ProfileService
from app.dependencies.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/me")
def my_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return ProfileService.get_my_profile(db, current_user)


@router.put("/me")
async def update_profile(
    bio: Optional[str] = Form(None),
    skills: Optional[list[str]] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await ProfileService.update_profile(
        bio, skills, profile_image, db, current_user
    )

