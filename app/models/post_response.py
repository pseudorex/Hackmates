# models/post_response.py

from sqlalchemy import Column, Integer, ForeignKey, Text, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ResponseStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class PostResponse(Base):
    __tablename__ = "post_responses"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"))
    responder_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    message = Column(Text, nullable=False)
    status = Column(Enum(ResponseStatus), default=ResponseStatus.pending)

    created_at = Column(DateTime, default=datetime.utcnow)

    # relations
    post = relationship("Post", backref="responses")
    responder = relationship("Users")
