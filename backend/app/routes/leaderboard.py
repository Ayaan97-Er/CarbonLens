import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.goal import Goal
from app.schemas.user import LeaderboardEntry
from app.services.sustainability_score import SustainabilityScoreService

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("", response_model=List[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)):
    """
    Get privacy-safe community leaderboard ranked by Sustainability Score.
    Exposes only public display handle, sustainability score, tier, and reduction %.
    """
    today = datetime.date.today()
    cur_month_start = datetime.date(today.year, today.month, 1)

    if today.month == 1:
        prev_month_start = datetime.date(today.year - 1, 12, 1)
        prev_month_end = datetime.date(today.year - 1, 12, 31)
    else:
        prev_month_start = datetime.date(today.year, today.month - 1, 1)
        prev_month_end = datetime.date(today.year, today.month, 1) - datetime.timedelta(days=1)

    users = db.query(User).filter(
        User.is_active == True,
        User.leaderboard_opt_in == True
    ).all()

    entries = []
    for u in users:
        # Current month co2
        cur_co2 = (
            db.query(func.sum(Activity.calculated_co2))
            .filter(
                Activity.user_id == u.id,
                Activity.activity_date >= cur_month_start,
            )
            .scalar()
            or 0.0
        )
        # Prev month co2
        prev_co2 = (
            db.query(func.sum(Activity.calculated_co2))
            .filter(
                Activity.user_id == u.id,
                Activity.activity_date >= prev_month_start,
                Activity.activity_date <= prev_month_end,
            )
            .scalar()
            or 0.0
        )

        goal = db.query(Goal).filter(Goal.user_id == u.id, Goal.is_active == True).first()

        score_detail = SustainabilityScoreService.calculate_score(
            db=db,
            user_id=u.id,
            current_month_emissions=cur_co2,
            previous_month_emissions=prev_co2,
            current_goal=goal,
        )

        score = score_detail["score"]

        # Calculate reduction %
        reduction_pct = 0.0
        if prev_co2 > 0:
            reduction_pct = max(-100.0, round(((prev_co2 - cur_co2) / prev_co2) * 100, 1))

        # Determine Tier
        if score >= 85:
            tier = "Eco Master"
        elif score >= 70:
            tier = "Green Champion"
        elif score >= 50:
            tier = "Sustainability Pioneer"
        else:
            tier = "Active Reducer"

        # Display name
        display_name = u.public_handle or (u.full_name.split()[0] + f"_{u.id % 1000}")

        entries.append({
            "display_name": display_name,
            "sustainability_score": score,
            "monthly_emissions_kg": round(float(cur_co2), 1),
            "reduction_percentage": reduction_pct,
            "tier": tier,
        })

    # Sort descending by score, then by reduction
    entries.sort(key=lambda x: (x["sustainability_score"], x["reduction_percentage"]), reverse=True)

    # Assign ranks
    result = []
    for idx, entry in enumerate(entries[:50]):  # Top 50
        result.append(LeaderboardEntry(
            rank=idx + 1,
            display_name=entry["display_name"],
            sustainability_score=entry["sustainability_score"],
            monthly_emissions_kg=entry["monthly_emissions_kg"],
            reduction_percentage=entry["reduction_percentage"],
            tier=entry["tier"],
        ))

    return result
