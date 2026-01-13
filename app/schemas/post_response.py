# schemas/post_response.py

from pydantic import BaseModel
from datetime import datetime


class PostResponseOut(BaseModel):
    id: int
    message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class UpdateResponseStatusSchema(BaseModel):
    status: str  # accepted | rejected

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


