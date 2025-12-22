from typing import List, Optional
from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    email: str
    firstName: str
    lastName: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class CompleteProfileRequest(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
