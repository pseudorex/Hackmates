from typing import List, Optional
from pydantic import BaseModel, Field


class CompleteProfileRequest(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
