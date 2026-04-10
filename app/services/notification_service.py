from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Optional, List, Any

from app.models.notification import Notification, NotificationType
from app.models.notification_preferences import NotificationPreference, NotificationFrequency
from app.schemas.notification_schema import NotificationCreate, NotificationUpdate

from app.core.websocket_manager import manager


class NotificationService:
    @staticmethod
    async def create_notification(
            db: Session,
            user_id: int,
            type: NotificationType,
            title: str,
            description: str,
            action_url: Optional[str] = None,
            metadata: Optional[dict[str, Any]] = None,
            expires_in_days: int = 30
    ) -> Optional[Notification]:
        # Check user preferences
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        # If no prefs, assume defaults (enabled)
        if prefs and not prefs.in_app_notifications_enabled:
            return None

        # Create notification
        notification = Notification(
            user_id=user_id,
            notification_type=type,
            title=title,
            description=description,
            action_url=action_url,
            metadata=metadata,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Trigger real-time emission (WebSocket)
        await manager.send_personal_message({
            "id": notification.id,
            "type": notification.notification_type,
            "title": notification.title,
            "description": notification.description,
            "action_url": notification.action_url,
            "metadata": notification.metadata,
            "created_at": notification.created_at.isoformat()
        }, user_id)

        return notification

    @staticmethod
    def get_notifications(
            db: Session,
            user_id: int,
            unread_only: bool = False,
            limit: int = 20,
            offset: int = 0
    ) -> List[Notification]:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)

        return query.order_by(desc(Notification.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.commit()
            db.refresh(notification)

        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        result = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            Notification.is_read: True,
            Notification.read_at: datetime.utcnow()
        }, synchronize_session=False)

        db.commit()
        return result

    @staticmethod
    def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if notification:
            db.delete(notification)
            db.commit()
            return True
        return False

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()

    @staticmethod
    def get_preferences(db: Session, user_id: int) -> NotificationPreference:
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)

        return prefs

    @staticmethod
    def update_preferences(
            db: Session,
            user_id: int,
            email_on_new_application: Optional[bool] = None,
            email_on_status_change: Optional[bool] = None,
            in_app_notifications_enabled: Optional[bool] = None,
            notification_frequency: Optional[NotificationFrequency] = None
    ) -> NotificationPreference:
        prefs = NotificationService.get_preferences(db, user_id)

        if email_on_new_application is not None:
            prefs.email_on_new_application = email_on_new_application
        if email_on_status_change is not None:
            prefs.email_on_status_change = email_on_status_change
        if in_app_notifications_enabled is not None:
            prefs.in_app_notifications_enabled = in_app_notifications_enabled
        if notification_frequency is not None:
            prefs.notification_frequency = notification_frequency

        db.commit()
        db.refresh(prefs)
        return prefs
