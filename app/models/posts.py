from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from datetime import datetime
from app.database import Base


from sqlalchemy.orm import relationship

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    duration = Column(String(50), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    creator = relationship("Users", backref="posts")

    images = relationship(
        "PostImage",
        backref="post",
        cascade="all, delete-orphan",
        lazy="joined"
    )

