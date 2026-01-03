from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.posts import Post


router = APIRouter(
    prefix="/feed",
    tags=["Feed"]
)

@router.get("/")
def get_feed(
    cursor: Optional[datetime] = Query(None),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Post).filter(Post.is_active == True)
    if cursor:
        query = query.filter(Post.created_at < cursor)

    posts = (
        query.order_by(Post.created_at.desc()).limit(limit + 1).all()
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
            "duration": post.duration,      # can be null
            "photo": post.photo,
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
            "next_cursor": next_cursor
        }
    }
