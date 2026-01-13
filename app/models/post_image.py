from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class PostImage(Base):
    __tablename__ = "post_images"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=False)

    post_id = Column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False
    )
