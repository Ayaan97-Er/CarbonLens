from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.recommendation import RecommendationsResponse
from app.auth.dependencies import get_current_user
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter(prefix="/recommendations", tags=["Smart Recommendations"])


@router.get("", response_model=RecommendationsResponse)
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get smart, deterministic, data-driven sustainability recommendations
    tailored to the user's real logging history.
    """
    data = RecommendationEngine.generate_recommendations(db=db, user_id=current_user.id)
    return data
