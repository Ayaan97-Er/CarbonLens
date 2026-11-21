from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.achievement import AchievementOut, AchievementsSummary
from app.auth.dependencies import get_current_user
from app.services.achievement_service import AchievementService

router = APIRouter(prefix="/achievements", tags=["Achievements & Milestones"])


@router.get("", response_model=AchievementsSummary)
def list_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all achievements with the current user's unlocked status,
    unlock timestamps, and progress percentages.
    """
    items = AchievementService.evaluate_user_achievements(db, current_user.id)
    unlocked_count = sum(1 for a in items if a["is_unlocked"])
    total_count = len(items)
    completion_pct = round((unlocked_count / total_count) * 100, 1) if total_count > 0 else 0.0

    return {
        "total_achievements": total_count,
        "unlocked_count": unlocked_count,
        "completion_percentage": completion_pct,
        "items": items,
    }


@router.get("/unlocked", response_model=List[AchievementOut])
def list_unlocked_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List only the badges and milestones unlocked by the user."""
    items = AchievementService.evaluate_user_achievements(db, current_user.id)
    return [a for a in items if a["is_unlocked"]]
