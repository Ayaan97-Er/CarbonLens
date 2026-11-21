import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.activity import Activity
from app.models.goal import Goal


class SustainabilityScoreService:
    @staticmethod
    def calculate_score(
        db: Session,
        user_id: int,
        current_month_emissions: float,
        previous_month_emissions: float,
        current_goal: Optional[Goal] = None
    ) -> Dict[str, Any]:
        """
        Calculate transparent 0-100 Sustainability Score.
        Returns detailed component breakdown and human-friendly explanation.
        """
        today = datetime.date.today()
        month_start = datetime.date(today.year, today.month, 1)

        # 1. Target Component (Max 35 points)
        target_pts = 22  # default if no goal set
        if current_goal and current_goal.monthly_target > 0:
            target = current_goal.monthly_target
            if current_month_emissions <= target:
                ratio = current_month_emissions / target
                # 35 points when 50% under budget, tapering smoothly
                target_pts = int(35 - (ratio * 10))
                target_pts = max(18, min(35, target_pts))
            else:
                over_ratio = (current_month_emissions - target) / target
                target_pts = max(0, int(20 - (over_ratio * 30)))

        # 2. MoM Trend Component (Max 30 points)
        trend_pts = 20  # default for new accounts
        if previous_month_emissions > 0:
            pct_change = (
                (current_month_emissions - previous_month_emissions)
                / previous_month_emissions
            ) * 100
            if pct_change <= -20:
                trend_pts = 30  # >20% reduction
            elif pct_change < 0:
                trend_pts = int(22 + (-pct_change / 20) * 8)  # 0 to 20% reduction
            elif pct_change == 0:
                trend_pts = 20
            elif pct_change <= 25:
                trend_pts = int(max(8, 20 - (pct_change / 25) * 10))
            else:
                trend_pts = max(2, int(10 - ((pct_change - 25) / 50) * 8))

        # 3. Tracking Consistency Component (Max 20 points)
        # Distinct days with logged activities this month
        distinct_days_count = (
            db.query(func.count(func.distinct(Activity.activity_date)))
            .filter(
                Activity.user_id == user_id,
                Activity.activity_date >= month_start,
                Activity.activity_date <= today,
            )
            .scalar()
            or 0
        )
        consistency_pts = min(20, distinct_days_count * 4)

        # 4. Mitigation & Green Choices Component (Max 15 points)
        # Count activities with low/zero carbon (e.g. Walking, Bicycle, Transit, Vegetarian, Vegan, Solar)
        green_keywords = ["Bicycle", "Walking", "Train", "Metro", "Transit", "Bus", "Vegan", "Vegetarian", "Renewable", "Solar", "EV"]
        green_activities_count = 0
        for kw in green_keywords:
            c = (
                db.query(func.count(Activity.id))
                .filter(
                    Activity.user_id == user_id,
                    Activity.activity_date >= month_start,
                    Activity.activity_type.ilike(f"%{kw}%"),
                )
                .scalar()
                or 0
            )
            green_activities_count += c

        mitigation_pts = min(15, green_activities_count * 3)

        # Sum and clamp to 0-100
        total_score = max(0, min(100, target_pts + trend_pts + consistency_pts + mitigation_pts))

        # Qualitative Rating
        if total_score >= 85:
            rating = "Outstanding"
            explanation = "Exceptional sustainability habits! You are well within targets and actively logging low-carbon choices."
        elif total_score >= 70:
            rating = "Great"
            explanation = "Solid environmental awareness with steady tracking and controlled carbon output."
        elif total_score >= 50:
            rating = "Moderate"
            explanation = "Good start. Focus on keeping within your monthly budget and swapping high-carbon trips for transit."
        else:
            rating = "Needs Improvement"
            explanation = "Your carbon footprint is elevated this month. Explore our recommendations to lower key emission drivers."

        return {
            "score": total_score,
            "rating": rating,
            "explanation": explanation,
            "target_component": target_pts,
            "trend_component": trend_pts,
            "consistency_component": consistency_pts,
            "mitigation_component": mitigation_pts,
        }
