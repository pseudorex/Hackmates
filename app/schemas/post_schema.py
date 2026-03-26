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
        from_attributes = True

class FeedCreator(BaseModel):
    id: Optional[int]
    username: Optional[str]
    profile_photo: Optional[str]

    class Config:
        from_attributes = True

class FeedPostResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    duration: Optional[str]
    images: List[str]
    creator: FeedCreator
    created_at: datetime

    class Config:
        from_attributes = True

class FeedPagination(BaseModel):
    limit: int
    has_next: bool
    next_cursor: Optional[str]

class FeedResponse(BaseModel):
    posts: List[FeedPostResponse]
    pagination: FeedPagination
