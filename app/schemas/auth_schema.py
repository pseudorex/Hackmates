from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    email: str
    firstName: str
    lastName: str
    password: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str
