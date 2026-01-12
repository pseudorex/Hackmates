from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.feed_service import FeedService

router = APIRouter(
    prefix="/feed",
    tags=["Feed"]
)

@router.get("/")
def get_feed(
    cursor: Optional[datetime] = Query(None),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return FeedService.get_feed(cursor, limit, db, current_user)
