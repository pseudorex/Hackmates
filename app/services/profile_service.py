import json
from typing import Optional
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from cloudinary.uploader import upload

from app.models.users import Users
from app.models.skills import Skills
from app.schemas.profile_schema import CompleteProfileRequest
from app.services.moderation_service import ModerationService


class ProfileService:

    @staticmethod
    async def complete_profile(
        bio: Optional[str],
        interests: Optional[str],
        profilePhoto: Optional[UploadFile],
        db: Session,
        current_user: dict
    ):

        text_to_check = f"{bio} {interests}"

        scores = ModerationService.analyze_text(text_to_check)

        if not ModerationService.is_allowed(scores):
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Bio or Skills contain malicious or toxic content",
                    "moderation score": scores
                }
            )


        skills = json.loads(interests) if interests else []

        profile = CompleteProfileRequest(bio=bio, skills=skills)
        user = db.query(Users).filter(Users.id == current_user["user_id"]).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.bio = profile.bio

        skill_objects = []
        for name in profile.skills:
            skill = db.query(Skills).filter(Skills.name == name).first()
            if not skill:
                skill = Skills(name=name)
                db.add(skill)
                db.flush()
            skill_objects.append(skill)

        user.skills = skill_objects

        if profilePhoto:
            user.profile_image = upload(profilePhoto.file)["secure_url"]

        db.commit()
        db.refresh(user)

        return {"message": "Profile updated"}
