from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.models import Users
from app.models.notification import NotificationType
from app.models.post_image import PostImage
from app.models.posts import Post
from app.models.post_response import PostResponse
from app.schemas.post_response import MyPostResponse
from app.services.moderation_service import ModerationService
from app.services.notification_service import NotificationService


class PostService:
    @staticmethod
    def create_post(
            db: Session,
            *,
            title: str,
            description: str,
            category: str,
            duration: str | None,
            photo_url: list[str] | None,
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
            created_by=created_by
        )

        db.add(post)
        db.flush()  # get post.id

        if photo_url:
            db.add_all([
                PostImage(image_url=url, post_id=post.id)
                for url in photo_url
            ])

        db.commit()

        # Reload with relationships in ONE query
        post = (
            db.query(Post)
            .options(
                joinedload(Post.creator),
                joinedload(Post.images)
            )
            .filter(Post.id == post.id)
            .first()
        )

        return post

    # Quick Apply
    @staticmethod
    async def quick_apply(db: Session, post_id: int, user_id: int):
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post.created_by == user_id:
            raise HTTPException(status_code=400, detail="Cannot apply to your own post")

        # NEW: Fetch user and check mobile
        user = db.query(Users).filter(Users.id == user_id).first()

        if not user.mobile:
            raise HTTPException(
                status_code=400,
                detail="Mobile number required before applying"
            )

        # Existing check
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

        # Increment application count
        post.application_count = (post.application_count or 0) + 1

        db.commit()
        db.refresh(response)
        db.refresh(post)

        # Notify Post Owner
        applicant = response.responder
        await NotificationService.create_notification(
            db=db,
            user_id=post.created_by,
            type=NotificationType.NEW_APPLICATION,
            title=f"New application on {post.title}",
            description=f"{applicant.username} applied just now",
            action_url=f"/posts/{post.id}/responses",
            metadata={
                "post_id": post.id,
                "post_title": post.title,
                "applicant_id": applicant.id,
                "applicant_name": applicant.username,
                "applicant_avatar": applicant.profile_image,
                "total_applications_on_post": post.application_count
            }
        )

        return {
            "message": "Quick apply successful",
            "status": "pending",
            "application_count": post.application_count
        }


    # Get Responses
    @staticmethod
    def get_post_responses(db: Session, post_id: int, user_id: int, limit: int = 10, offset: int = 0):
        post = db.query(Post).filter(Post.id == post_id).first()

        if not post or post.created_by != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        responses = (
            db.query(PostResponse, Users)
            .join(Users, Users.id == PostResponse.responder_id)
            .filter(PostResponse.post_id == post_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            {
                "response_id": response.id,
                "user_id": user.id,
                "username": user.username,
                "mobile": user.mobile,
                "status": response.status,
                "message": response.message,
                "created_at": response.created_at
            }
            for response, user in responses
        ]

    # Update Response Status
    @staticmethod
    async def update_response_status(
        db: Session,
        response_id: int,
        status: str,
        user_id: int,
        owner_response_message: str | None = None
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

        # Update status and review info
        response.status = status
        response.reviewed_at = datetime.utcnow()
        response.reviewed_by = user_id
        response.owner_response_message = owner_response_message

        db.commit()
        db.refresh(response)

            # Notify Applicant
        notif_type = NotificationType.APPLICATION_APPROVED
        if status == "rejected":
            notif_type = NotificationType.APPLICATION_REJECTED
        elif status == "shortlisted":
            notif_type = NotificationType.APPLICATION_SHORTLISTED

        await NotificationService.create_notification(
            db=db,
            user_id=response.responder_id,
            type=notif_type,
            title=f"Your application has been {status}",
            description=f"{post.title} - {post.creator.username}",
            action_url=f"/posts/{post.id}",
            metadata={
                "post_id": post.id,
                "post_title": post.title,
                "owner_id": post.creator.id,
                "owner_name": post.creator.username,
                "owner_avatar": post.creator.profile_image,
                "status": status,
                "message": owner_response_message
            }
        )

        return {
            "message": f"Response {status}",
            "chat_enabled": True if status == "accepted" else False,
            "status": status
        }

    # My Posts
    from app.schemas.post_response import MyPostResponse

    @staticmethod
    def get_my_posts(
            db: Session,
            user_id: int,
            limit: int = 10,
            offset: int = 0
    ):
        posts = (
            db.query(Post)
            .filter(Post.created_by == user_id)
            .order_by(desc(Post.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            MyPostResponse(
                id=post.id,
                title=post.title,
                description=post.description,
                category=post.category,
                duration=post.duration,
                images=[img.image_url for img in post.images],
                created_at=post.created_at
            )
            for post in posts
        ]

