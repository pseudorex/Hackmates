# schemas/post_response.py

from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class ResponseStatusEnum(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    shortlisted = "shortlisted"

class PostResponseOut(BaseModel):
    id: int
    message: str
    status: ResponseStatusEnum
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    owner_response_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UpdateResponseStatusSchema(BaseModel):
    status: ResponseStatusEnum  # accepted | rejected | shortlisted
    owner_response_message: Optional[str] = None

class MyPostResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    duration: str | None
    images: list[str] | None
    created_at: datetime

    class Config:
        from_attributes = True


