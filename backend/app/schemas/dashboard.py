from typing import List, Optional
from pydantic import BaseModel
from app.schemas.activity import ActivityOut
from app.schemas.goal import GoalProgressOut


class CategoryEmissions(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    icon: Optional[str] = None
    total_co2: float
    percentage: float
    activity_count: int


class MonthlyTrendPoint(BaseModel):
    month_str: str  # "Jan 2026", "Feb 2026"
    year: int
    month: int
    total_co2: float
    target_co2: Optional[float] = None
    activity_count: int


class DailyEmissionsPoint(BaseModel):
    date_str: str  # "2026-03-01"
    day_name: str  # "Mon", "Tue"
    total_co2: float
    activity_count: int


class SustainabilityScoreDetail(BaseModel):
    score: int  # 0 - 100
    rating: str  # "Outstanding", "Great", "Moderate", "Needs Improvement"
    explanation: str
    target_component: int  # 0-35
    trend_component: int  # 0-30
    consistency_component: int  # 0-20
    mitigation_component: int  # 0-15


class DashboardSummary(BaseModel):
    total_monthly_emissions: float  # kg CO2e for current month
    previous_month_emissions: float  # kg CO2e for last month
    percentage_change: float  # MoM % change (- means reduction, + means increase)
    daily_average: float  # Current month daily average in kg CO2e
    largest_category: Optional[str] = None
    largest_category_percentage: Optional[float] = None
    total_lifetime_emissions: float
    total_activities_count: int
    goal: GoalProgressOut
    sustainability_score: SustainabilityScoreDetail
    categories_breakdown: List[CategoryEmissions]
    monthly_trend: List[MonthlyTrendPoint]
    recent_daily_emissions: List[DailyEmissionsPoint]
    recent_activities: List[ActivityOut]
