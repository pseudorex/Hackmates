import json
from typing import Optional
from fastapi import HTTPException, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session
from cloudinary.uploader import upload

from app.models import Post
from app.models.users import Users
from app.models.skills import Skills
from app.schemas.profile_schema import CompleteProfileRequest
from app.services.moderation_service import ModerationService


class ProfileService:

    @staticmethod
    def _process_skills(skills: list[str], db: Session):
        skill_objects = []

        for name in skills:
            skill = db.query(Skills).filter(Skills.name == name).first()
            if not skill:
                skill = Skills(name=name)
                db.add(skill)
                db.flush()
            skill_objects.append(skill)

        return skill_objects


    @staticmethod
    async def complete_profile(
            bio: Optional[str],
            interests: Optional[str],
            profilePhoto: Optional[UploadFile],
            db: Session,
            current_user: dict
    ):
        text_to_check = f"{bio or ''} {interests or ''}"

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

        user = db.query(Users).filter(
            Users.id == current_user["user_id"]
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.bio = bio
        user.skills = ProfileService._process_skills(skills, db)

        if profilePhoto:
            user.profile_image = upload(profilePhoto.file)["secure_url"]

        db.commit()
        db.refresh(user)

        return {"message": "Profile completed successfully"}


    # Fetch Profile
    @staticmethod
    def get_my_profile(db: Session, current_user: dict):
        user = (
            db.query(Users)
            .filter(Users.id == current_user["user_id"])
            .first()
        )

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "username": user.username,
            "bio": user.bio,
            "profile_image": user.profile_image,
            "skills": [skill.name for skill in user.skills]
        }

    @staticmethod
    async def update_profile(
            bio: Optional[str],
            skills: Optional[str],
            profile_image: Optional[UploadFile],
            db: Session,
            current_user: dict
    ):
        user = db.query(Users).filter(
            Users.id == current_user["user_id"]
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # BIO UPDATE
        if bio is not None:
            scores = ModerationService.analyze_text(bio)
            if not ModerationService.is_allowed(scores):
                raise HTTPException(
                    status_code=400,
                    detail="Bio contains restricted content"
                )
            user.bio = bio

        # SKILLS UPDATE
        if skills is not None:
            skill_list = json.loads(skills)
            user.skills = ProfileService._process_skills(skill_list, db)

        # IMAGE UPDATE
        if profile_image:
            user.profile_image = upload(profile_image.file)["secure_url"]

        db.commit()
        db.refresh(user)

        return {"message": "Profile updated successfully"}




