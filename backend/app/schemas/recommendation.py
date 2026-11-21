from typing import List, Optional
from pydantic import BaseModel


class RecommendationOut(BaseModel):
    id: str
    category_name: str
    category_icon: Optional[str] = None
    title: str
    description: str
    impact_level: str  # "high", "medium", "low"
    potential_monthly_savings_kg: float
    actionable_step: str
    relevance_reason: str


class RecommendationsResponse(BaseModel):
    recommendations: List[RecommendationOut]
    total_potential_monthly_savings_kg: float
    total_potential_annual_savings_kg: float
    dominant_category: Optional[str] = None
