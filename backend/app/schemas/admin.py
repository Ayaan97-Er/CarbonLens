from typing import List, Optional
from pydantic import BaseModel
from app.schemas.user import UserOut
from app.schemas.category import EmissionFactorOut


class AdminUserOut(UserOut):
    total_activities: int
    total_emissions_kg: float


class AdminUserUpdateRole(BaseModel):
    role: str  # "user" | "admin"
    is_active: bool


class SystemStatsOut(BaseModel):
    total_users: int
    active_users: int
    total_activities_logged: int
    total_emissions_tracked_kg: float
    total_goals_set: int
    total_achievements_unlocked: int
    categories_count: int
    factors_count: int
