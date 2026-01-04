from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.posts import Post
from app.services.moderation_service import ModerationService
class PostService:

    @staticmethod
    def create_post(
        db: Session,
        *,
        title: str,
        description: str,
        category: str,
        duration: str | None,
        photo_url: str | None,
        created_by: int
    ) -> Post:

        text_to_check = f"{title} {description}"

        scores = ModerationService.analyze_text(text_to_check)

        if not ModerationService.is_allowed(scores):
            raise HTTPException(
                status_code=400,
                detail={
                    "message" : "Post contain malicious or toxic content",
                    "moderation score" : scores
                }
            )


        post = Post(
            title=title,
            description=description,
            category=category,
            duration=duration,
            photo=photo_url,
            created_by=created_by
        )

        db.add(post)
        db.commit()
        db.refresh(post)

        return post
