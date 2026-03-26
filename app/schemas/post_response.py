# schemas/post_response.py

from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class ResponseStatusEnum(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class PostResponseOut(BaseModel):
    id: int
    message: str
    status: ResponseStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True

class UpdateResponseStatusSchema(BaseModel):
    status: ResponseStatusEnum  # accepted | rejected

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


