from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
import enum
from app.database import Base


class NotificationFrequency(str, enum.Enum):
    INSTANT = "INSTANT"
    DAILY_DIGEST = "DAILY_DIGEST"
    WEEKLY_DIGEST = "WEEKLY_DIGEST"


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    email_on_new_application = Column(Boolean, default=True)
    email_on_status_change = Column(Boolean, default=True)
    in_app_notifications_enabled = Column(Boolean, default=True)

    notification_frequency = Column(
        Enum(NotificationFrequency), default=NotificationFrequency.INSTANT
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
