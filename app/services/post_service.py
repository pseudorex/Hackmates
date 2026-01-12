from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.posts import Post
from app.models.post_response import PostResponse
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
                    "message": "Post contains malicious or toxic content",
                    "moderation_score": scores
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

    # Quick Apply
    @staticmethod
    def quick_apply(db: Session, post_id: int, user_id: int):
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post.created_by == user_id:
            raise HTTPException(status_code=400, detail="Cannot apply to your own post")

        existing = db.query(PostResponse).filter(
            PostResponse.post_id == post_id,
            PostResponse.responder_id == user_id
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Already applied")

        response = PostResponse(
            post_id=post_id,
            responder_id=user_id,
            message="Quick applied"
        )

        db.add(response)
        db.commit()

        return {
            "message": "Quick apply successful",
            "status": "pending"
        }

    # Get Responses
    @staticmethod
    def get_post_responses(db: Session, post_id: int, user_id: int):
        post = db.query(Post).filter(Post.id == post_id).first()

        if not post or post.created_by != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return db.query(PostResponse).filter(
            PostResponse.post_id == post_id
        ).all()

    # Update Response Status
    @staticmethod
    def update_response_status(
        db: Session,
        response_id: int,
        status: str,
        user_id: int
    ):
        response = db.query(PostResponse).filter(
            PostResponse.id == response_id
        ).first()

        if not response:
            raise HTTPException(status_code=404, detail="Response not found")

        post = db.query(Post).filter(
            Post.id == response.post_id
        ).first()

        if post.created_by != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        response.status = status
        db.commit()

        return {
            "message": f"Response {status}",
            "chat_enabled": False
        }

    # My Posts
    @staticmethod
    def get_my_posts(
        db: Session,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ):
        return (
            db.query(Post)
            .filter(Post.created_by == user_id)
            .order_by(desc(Post.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
