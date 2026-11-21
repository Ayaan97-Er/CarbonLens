import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    leaderboard_opt_in: bool = True
    public_handle: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: str = "user"


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    leaderboard_opt_in: Optional[bool] = None
    public_handle: Optional[str] = None


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    leaderboard_opt_in: bool
    public_handle: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    rank: int
    display_name: str
    sustainability_score: int
    monthly_emissions_kg: float
    reduction_percentage: float
    tier: str  # "Eco Master", "Green Champion", "Sustainability Pioneer", "Active Reducer"
