from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.auth.dependencies import get_current_user
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve full aggregated dashboard data:
    - Monthly total kg CO2e
    - MoM percentage change
    - Daily average
    - Goal progress
    - Sustainability score
    - Category breakdown
    - Monthly trend history
    - Recent daily activity
    - Recent activities list
    """
    summary = DashboardService.get_dashboard_summary(db=db, user_id=current_user.id)
    return summary


@router.get("/category-breakdown")
def get_category_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve category breakdown for doughnut visualization."""
    summary = DashboardService.get_dashboard_summary(db=db, user_id=current_user.id)
    return summary["categories_breakdown"]


@router.get("/monthly-trend")
def get_monthly_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve 6-month trend data for trend line/bar charts."""
    summary = DashboardService.get_dashboard_summary(db=db, user_id=current_user.id)
    return summary["monthly_trend"]


@router.get("/recent-activities")
def get_recent_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve latest 10 activities for quick dashboard display."""
    summary = DashboardService.get_dashboard_summary(db=db, user_id=current_user.id)
    return summary["recent_activities"]
