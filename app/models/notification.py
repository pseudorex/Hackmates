from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from app.database import Base
import enum


class NotificationType(str, enum.Enum):
    NEW_APPLICATION = "NEW_APPLICATION"
    APPLICATION_APPROVED = "APPLICATION_APPROVED"
    APPLICATION_REJECTED = "APPLICATION_REJECTED"
    APPLICATION_SHORTLISTED = "APPLICATION_SHORTLISTED"
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    notification_type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=False)

    is_read = Column(Boolean, default=False)
    action_url = Column(String(500), nullable=True)
    extra_data = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
