from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.notification_service import NotificationService
from app.schemas.notification_schema import (
    NotificationResponse,
    UnreadCountResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return NotificationService.get_notifications(
        db=db,
        user_id=current_user["user_id"],
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    count = NotificationService.get_unread_count(db, current_user["user_id"])
    return {"unread_count": count}


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_preferences(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    return NotificationService.get_preferences(db, current_user["user_id"])


@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_preferences(
    payload: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return NotificationService.update_preferences(
        db=db,
        user_id=current_user["user_id"],
        email_on_new_application=payload.email_on_new_application,
        email_on_status_change=payload.email_on_status_change,
        in_app_notifications_enabled=payload.in_app_notifications_enabled,
        notification_frequency=payload.notification_frequency,
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = NotificationService.mark_as_read(
        db, notification_id, current_user["user_id"]
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = NotificationService.mark_as_read(
        db, notification_id, current_user["user_id"]
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.put("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    count = NotificationService.mark_all_as_read(db, current_user["user_id"])
    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = NotificationService.delete_notification(
        db, notification_id, current_user["user_id"]
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted successfully"}
