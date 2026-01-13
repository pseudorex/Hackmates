from pydantic import BaseModel
from typing import Optional, List
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
    images: List[str]
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True
