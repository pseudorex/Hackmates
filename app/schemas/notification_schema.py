from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any
from app.models.notification import NotificationType
import enum



class NotificationFrequency(str, enum.Enum):
    INSTANT = "INSTANT"
    DAILY_DIGEST = "DAILY_DIGEST"
    WEEKLY_DIGEST = "WEEKLY_DIGEST"


class NotificationBase(BaseModel):
    notification_type: NotificationType
    title: str
    description: str
    action_url: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    unread_count: int


class NotificationPreferenceBase(BaseModel):
    email_on_new_application: bool = True
    email_on_status_change: bool = True
    in_app_notifications_enabled: bool = True
    notification_frequency: NotificationFrequency = NotificationFrequency.INSTANT


class NotificationPreferenceUpdate(BaseModel):
    email_on_new_application: Optional[bool] = None
    email_on_status_change: Optional[bool] = None
    in_app_notifications_enabled: Optional[bool] = None
    notification_frequency: Optional[NotificationFrequency] = None


class NotificationPreferenceResponse(NotificationPreferenceBase):
    user_id: int
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
