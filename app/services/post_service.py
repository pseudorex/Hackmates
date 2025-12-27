from sqlalchemy.orm import Session
from app.models.posts import Post

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
