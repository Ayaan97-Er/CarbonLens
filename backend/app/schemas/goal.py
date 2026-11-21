import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GoalBase(BaseModel):
    monthly_target: float = Field(..., gt=0, description="Target monthly footprint in kg CO2e")
    start_date: datetime.date = Field(default_factory=datetime.date.today)
    end_date: Optional[datetime.date] = None


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    monthly_target: Optional[float] = Field(None, gt=0)
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    is_active: Optional[bool] = None


class GoalOut(GoalBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class GoalProgressOut(BaseModel):
    has_active_goal: bool
    monthly_target: Optional[float] = None
    current_month_emissions: float
    remaining_budget: Optional[float] = None
    percentage_used: Optional[float] = None
    status: str  # "on_track", "caution", "exceeded", "no_goal"
    status_message: str
