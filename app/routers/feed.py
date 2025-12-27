from fastapi import APIRouter, Depends
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    posts = (
        db.query(Post)
        .filter(Post.is_active == True)
        .order_by(Post.created_at.desc())
        .limit(20)
        .all()
    )

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

    return {"posts": response}
