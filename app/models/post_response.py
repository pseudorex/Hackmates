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
    shortlisted = "shortlisted"


class PostResponse(Base):
    __tablename__ = "post_responses"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"))
    responder_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    message = Column(Text, nullable=False)
    status = Column(Enum(ResponseStatus), default=ResponseStatus.pending)

    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner_response_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # relations
    post = relationship("Post", backref="responses")

    responder = relationship(
        "Users",
        foreign_keys=[responder_id],
        backref="responses_given"
    )

    reviewer = relationship(
        "Users",
        foreign_keys=[reviewed_by],
        backref="responses_reviewed"
    )
