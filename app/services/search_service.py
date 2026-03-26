from sqlalchemy.orm import Session
from sqlalchemy import asc, or_
from app.models.skills import Skills
from app.models.posts import Post


class SearchService:
    @staticmethod
    def search_skills(
            db: Session,
            query: str,
            limit: int = 8
    ):
        # Get prefix matches
        prefix = (
            db.query(Skills)
            .filter(Skills.name.ilike(f"{query}%"))
            .order_by(asc(Skills.name))
            .limit(limit)
            .all()
        )

        # If we have enough prefix matches, return early
        if len(prefix) >= limit:
            return prefix

        # Get IDs of prefix matches to exclude from fuzzy search
        prefix_ids = {skill.id for skill in prefix}

        # Get fuzzy matches (excluding prefix matches)
        remaining_needed = limit - len(prefix)
        fuzzy = (
            db.query(Skills)
            .filter(
                Skills.name.ilike(f"%{query}%"),
                ~Skills.name.ilike(f"{query}%"),  # Exclude prefix matches
                ~Skills.id.in_(prefix_ids)  # Also exclude by ID for safety
            )
            .order_by(asc(Skills.name))
            .limit(remaining_needed)
            .all()
        )

        return prefix + fuzzy

    @staticmethod
    def search_category(
            db: Session,
            query: str,
            limit: int = 8
    ):

        # Get prefix matches
        prefix = (
            db.query(Post)
            .filter(Post.category.ilike(f"{query}%"))
            .order_by(asc(Post.category))
            .limit(limit)
            .all()
        )

        # If we have enough prefix matches, return early
        if len(prefix) >= limit:
            return prefix

        # Get IDs of prefix matches to exclude from fuzzy search
        prefix_ids = {post.id for post in prefix}

        # Get fuzzy matches (excluding prefix matches)
        remaining_needed = limit - len(prefix)
        fuzzy = (
            db.query(Post)
            .filter(
                Post.category.ilike(f"%{query}%"),
                ~Post.category.ilike(f"{query}%"),  # Exclude prefix matches
                ~Post.id.in_(prefix_ids)  # Also exclude by ID for safety
            )
            .order_by(asc(Post.category))
            .limit(remaining_needed)
            .all()
        )

        return prefix + fuzzy

    @staticmethod
    def search_all(
            db: Session,
            query: str,
            limit: int = 8
    ):

        skills = SearchService.search_skills(db, query, limit)
        categories = SearchService.search_category(db, query, limit)

        return {
            "skills": skills,
            "categories": categories
        }