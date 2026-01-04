from sqlalchemy.orm import Session
from sqlalchemy import asc
from app.models.skills import Skills
from app.models.posts import Post


class SearchService:
    @staticmethod
    def search_skills(
        db: Session,
        query: str,
        limit: int = 8
    ):
        prefix = (
            db.query(Skills)
            .filter(Skills.name.ilike(f"{query}%"))
            .order_by(asc(Skills.name))
            .limit(limit)
            .all()
        )

        if len(prefix) >= limit:
            return prefix

        fuzzy = (
            db.query(Skills)
            .filter(
                Skills.name.ilike(f"%{query}%"),
                ~Skills.name.ilike(f"{query}%")
            )
            .order_by(asc(Skills.name))
            .limit(limit - len(prefix))
            .all()
        )

        return prefix + fuzzy


    def search_category(
            db: Session,
            query: str,
            limit: int = 8
    ):
        prefix = (
            db.query(Post)
            .filter(Post.category.ilike(f"{query}%"))
            .order_by(asc(Post.category))
            .limit(limit)
            .all()
        )

        if len(prefix) >= limit:
            return prefix

        fuzzy = (
            db.query(Post)
            .filter(
                Post.category.ilike(f"%{query}%"),
                ~Post.category.ilike(f"{query}%")
            )
            .order_by(asc(Post.category))
            .limit(limit - len(prefix))
            .all()
        )

        return prefix + fuzzy
