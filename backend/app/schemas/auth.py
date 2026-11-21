from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="User password")


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, description="Full name of user")
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100, description="Password with minimum 6 characters")
    public_handle: Optional[str] = Field(None, max_length=50, description="Optional public handle for leaderboard")


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6, max_length=100)
