from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CreatePostRequest(BaseModel):
    title: str
    description: str
    category: str
    duration: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    duration: Optional[str]
    photo: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True
