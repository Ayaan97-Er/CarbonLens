import datetime
from typing import List, Optional
from pydantic import BaseModel


class AchievementOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    icon: str
    badge_tier: str
    requirement_type: str
    requirement_value: float
    is_unlocked: bool = False
    unlocked_at: Optional[datetime.datetime] = None
    progress_percentage: float = 0.0
    current_progress: float = 0.0

    class Config:
        from_attributes = True


class UserAchievementOut(BaseModel):
    id: int
    user_id: int
    achievement_id: int
    unlocked_at: datetime.datetime
    achievement: AchievementOut

    class Config:
        from_attributes = True


class AchievementsSummary(BaseModel):
    total_achievements: int
    unlocked_count: int
    completion_percentage: float
    items: List[AchievementOut]
