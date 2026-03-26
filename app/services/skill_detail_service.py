from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from app.models.skills import Skills
from app.models.posts import Post
from app.models.users import Users
from typing import Dict, List, Any


class SkillDetailService:

    @staticmethod
    def get_skill_details(db: Session, skill_name: str) -> Dict[str, Any]:
        # Case-insensitive partial match
        skill = (
            db.query(Skills)
            .filter(Skills.name.ilike(f"%{skill_name}%"))
            .first()
        )

        if not skill:
            return {
                "found": False,
                "message": f"Skill '{skill_name}' not found"
            }

        # Get users with JOIN (optimized)
        users_with_skill = (
            db.query(Users)
            .join(Users.skills)
            .filter(Skills.id == skill.id, Users.is_active == True)
            .all()
        )

        # Limit initial response (important)
        users_with_skill = users_with_skill[:20]

        # Get posts with JOIN + eager loading
        posts = (
            db.query(Post)
            .options(joinedload(Post.creator))
            .join(Users, Post.created_by == Users.id)
            .join(Users.skills)
            .filter(
                Skills.id == skill.id,
                Post.is_active == True
            )
            .order_by(desc(Post.created_at))
            .limit(20)
            .all()
        )

        # Counts (optimized)
        total_accounts = (
            db.query(func.count(Users.id))
            .join(Users.skills)
            .filter(Skills.id == skill.id, Users.is_active == True)
            .scalar()
        )

        total_posts = (
            db.query(func.count(Post.id))
            .join(Users, Post.created_by == Users.id)
            .join(Users.skills)
            .filter(Skills.id == skill.id, Post.is_active == True)
            .scalar()
        )

        return {
            "found": True,
            "skill": {
                "id": skill.id,
                "name": skill.name,
            },
            "accounts": [
                {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "bio": user.bio,
                    "profile_image": user.profile_image,
                    "is_verified": user.is_verified,
                }
                for user in users_with_skill
            ],
            "posts": [
                {
                    "id": post.id,
                    "title": post.title,
                    "description": post.description,
                    "category": post.category,
                    "duration": post.duration,
                    "created_at": post.created_at.isoformat() if post.created_at else None,
                    "creator": {
                        "id": post.creator.id,
                        "username": post.creator.username,
                        "first_name": post.creator.first_name,
                        "last_name": post.creator.last_name,
                        "profile_image": post.creator.profile_image,
                    }
                }
                for post in posts
            ],
            "stats": {
                "total_accounts": total_accounts,
                "total_posts": total_posts,
            }
        }

    @staticmethod
    def get_skill_accounts(
        db: Session,
        skill_name: str,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:

        skill = (
            db.query(Skills)
            .filter(Skills.name.ilike(f"%{skill_name}%"))
            .first()
        )

        if not skill:
            return {"found": False, "accounts": [], "total": 0}

        total = (
            db.query(func.count(Users.id))
            .join(Users.skills)
            .filter(Skills.id == skill.id, Users.is_active == True)
            .scalar()
        )

        accounts = (
            db.query(Users)
            .join(Users.skills)
            .filter(Skills.id == skill.id, Users.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

        return {
            "found": True,
            "skill_name": skill.name,
            "accounts": [
                {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "bio": user.bio,
                    "profile_image": user.profile_image,
                    "is_verified": user.is_verified,
                }
                for user in accounts
            ],
            "skip": skip,
            "limit": limit,
            "total": total
        }

    @staticmethod
    def get_skill_posts(
        db: Session,
        skill_name: str,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:

        skill = (
            db.query(Skills)
            .filter(Skills.name.ilike(f"%{skill_name}%"))
            .first()
        )

        if not skill:
            return {"found": False, "posts": [], "total": 0}

        total = (
            db.query(func.count(Post.id))
            .join(Users, Post.created_by == Users.id)
            .join(Users.skills)
            .filter(Skills.id == skill.id, Post.is_active == True)
            .scalar()
        )

        posts = (
            db.query(Post)
            .options(joinedload(Post.creator))
            .join(Users, Post.created_by == Users.id)
            .join(Users.skills)
            .filter(Skills.id == skill.id, Post.is_active == True)
            .order_by(desc(Post.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return {
            "found": True,
            "skill_name": skill.name,
            "posts": [
                {
                    "id": post.id,
                    "title": post.title,
                    "description": post.description,
                    "category": post.category,
                    "duration": post.duration,
                    "created_at": post.created_at.isoformat() if post.created_at else None,
                    "creator": {
                        "id": post.creator.id,
                        "username": post.creator.username,
                        "first_name": post.creator.first_name,
                        "last_name": post.creator.last_name,
                        "profile_image": post.creator.profile_image,
                    }
                }
                for post in posts
            ],
            "skip": skip,
            "limit": limit,
            "total": total
        }