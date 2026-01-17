from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.posts import Post


class FeedService:

    @staticmethod
    def get_feed(
        cursor: Optional[datetime],
        limit: int,
        db: Session,
        current_user: dict,
    ):
        from sqlalchemy.orm import joinedload

        query = (
            db.query(Post)
            .options(
                joinedload(Post.creator),  # FIX creator N+1
                joinedload(Post.images)  # already joined, safe
            )
            .filter(Post.is_active == True)
        )

        if cursor:
            query = query.filter(Post.created_at < cursor)

        posts = (
            query
            .order_by(Post.created_at.desc())
            .limit(limit + 1)
            .all()
        )

        has_next = len(posts) > limit
        posts = posts[:limit]

        next_cursor = posts[-1].created_at if posts else None

        response = []

        for post in posts:
            response.append({
                "id": post.id,
                "title": post.title,
                "description": post.description,
                "category": post.category,
                "duration": post.duration,
                "images": [
                    image.image_url for image in post.images
                ],
                "creator": {
                    "id": post.creator.id if post.creator else None,
                    "username": post.creator.username if post.creator else None,
                    "profile_photo": post.creator.profile_image if post.creator else None
                },
                "created_at": post.created_at
            })

        return {
            "posts": response,
            "pagination": {
                "limit": limit,
                "has_next": has_next,
                "next_cursor": next_cursor.isoformat() if next_cursor else None
            }
        }
