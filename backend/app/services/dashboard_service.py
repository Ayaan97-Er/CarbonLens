import datetime
import calendar
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract
from app.models.activity import Activity
from app.models.category import Category
from app.models.goal import Goal
from app.services.sustainability_score import SustainabilityScoreService


class DashboardService:
    @staticmethod
    def get_month_date_range(year: int, month: int):
        """Return (first_day, last_day) of given month."""
        first_day = datetime.date(year, month, 1)
        last_day_num = calendar.monthrange(year, month)[1]
        last_day = datetime.date(year, month, last_day_num)
        return first_day, last_day

    @staticmethod
    def get_dashboard_summary(db: Session, user_id: int) -> Dict[str, Any]:
        """Aggregate full dashboard data with optimized SQL queries."""
        today = datetime.date.today()
        cur_year, cur_month = today.year, today.month
        cur_first, cur_last = DashboardService.get_month_date_range(cur_year, cur_month)

        # Previous month
        if cur_month == 1:
            prev_year, prev_month = cur_year - 1, 12
        else:
            prev_year, prev_month = cur_year, cur_month - 1
        prev_first, prev_last = DashboardService.get_month_date_range(prev_year, prev_month)

        # 1. Current Month Total Emissions
        cur_emissions = (
            db.query(func.sum(Activity.calculated_co2))
            .filter(
                Activity.user_id == user_id,
                Activity.activity_date >= cur_first,
                Activity.activity_date <= cur_last,
            )
            .scalar()
            or 0.0
        )
        cur_emissions = round(float(cur_emissions), 2)

        # 2. Previous Month Total Emissions
        prev_emissions = (
            db.query(func.sum(Activity.calculated_co2))
            .filter(
                Activity.user_id == user_id,
                Activity.activity_date >= prev_first,
                Activity.activity_date <= prev_last,
            )
            .scalar()
            or 0.0
        )
        prev_emissions = round(float(prev_emissions), 2)

        # 3. MoM Percentage Change
        if prev_emissions > 0:
            percentage_change = round(((cur_emissions - prev_emissions) / prev_emissions) * 100, 1)
        else:
            percentage_change = 0.0

        # 4. Daily Average this month
        days_in_current_month_so_far = max(1, today.day)
        daily_average = round(cur_emissions / days_in_current_month_so_far, 2)

        # 5. Lifetime metrics
        total_lifetime = (
            db.query(func.sum(Activity.calculated_co2))
            .filter(Activity.user_id == user_id)
            .scalar()
            or 0.0
        )
        total_lifetime = round(float(total_lifetime), 2)

        total_activities_count = (
            db.query(func.count(Activity.id))
            .filter(Activity.user_id == user_id)
            .scalar()
            or 0
        )

        # 6. Active Goal
        active_goal = (
            db.query(Goal)
            .filter(Goal.user_id == user_id, Goal.is_active == True)
            .order_by(Goal.created_at.desc())
            .first()
        )

        goal_data = {
            "has_active_goal": bool(active_goal),
            "monthly_target": active_goal.monthly_target if active_goal else None,
            "current_month_emissions": cur_emissions,
            "remaining_budget": round(active_goal.monthly_target - cur_emissions, 2) if active_goal else None,
            "percentage_used": round((cur_emissions / active_goal.monthly_target) * 100, 1) if active_goal and active_goal.monthly_target > 0 else None,
            "status": "no_goal",
            "status_message": "No active monthly target set. Set a goal to track your budget!",
        }

        if active_goal:
            target = active_goal.monthly_target
            if cur_emissions <= target * 0.8:
                goal_data["status"] = "on_track"
                goal_data["status_message"] = f"Great work! You are {round(target - cur_emissions, 1)} kg CO2e below your monthly target."
            elif cur_emissions <= target:
                goal_data["status"] = "caution"
                goal_data["status_message"] = f"Approaching limit: {round(target - cur_emissions, 1)} kg CO2e remaining this month."
            else:
                goal_data["status"] = "exceeded"
                goal_data["status_message"] = f"You are currently {round(cur_emissions - target, 1)} kg CO2e above your monthly target."

        # 7. Category Breakdown (Current Month, or Lifetime if cur month has 0)
        category_query = (
            db.query(
                Category.id,
                Category.name,
                Category.icon,
                func.sum(Activity.calculated_co2).label("cat_total"),
                func.count(Activity.id).label("cat_count"),
            )
            .join(Activity, Activity.category_id == Category.id)
            .filter(
                Activity.user_id == user_id,
                Activity.activity_date >= cur_first,
                Activity.activity_date <= cur_last,
            )
            .group_by(Category.id, Category.name, Category.icon)
            .order_by(desc("cat_total"))
            .all()
        )

        # Fallback to last 60 days if current month is empty to avoid blank charts
        if not category_query and total_activities_count > 0:
            category_query = (
                db.query(
                    Category.id,
                    Category.name,
                    Category.icon,
                    func.sum(Activity.calculated_co2).label("cat_total"),
                    func.count(Activity.id).label("cat_count"),
                )
                .join(Activity, Activity.category_id == Category.id)
                .filter(Activity.user_id == user_id)
                .group_by(Category.id, Category.name, Category.icon)
                .order_by(desc("cat_total"))
                .all()
            )

        cat_sum = sum([item.cat_total for item in category_query]) or 1.0
        categories_breakdown = []
        largest_cat_name = None
        largest_cat_pct = None

        for idx, cat in enumerate(category_query):
            pct = round((float(cat.cat_total) / cat_sum) * 100, 1)
            if idx == 0:
                largest_cat_name = cat.name
                largest_cat_pct = pct
            categories_breakdown.append({
                "category_id": cat.id,
                "category_name": cat.name,
                "icon": cat.icon or "leaf",
                "total_co2": round(float(cat.cat_total), 2),
                "percentage": pct,
                "activity_count": cat.cat_count,
            })

        # 8. Monthly Trend (Past 6 Months)
        monthly_trend = []
        for i in range(5, -1, -1):
            m_date = today.replace(day=1) - datetime.timedelta(days=i * 30)
            m_first, m_last = DashboardService.get_month_date_range(m_date.year, m_date.month)
            month_label = m_first.strftime("%b %Y")
            
            m_total = (
                db.query(func.sum(Activity.calculated_co2))
                .filter(
                    Activity.user_id == user_id,
                    Activity.activity_date >= m_first,
                    Activity.activity_date <= m_last,
                )
                .scalar()
                or 0.0
            )
            m_count = (
                db.query(func.count(Activity.id))
                .filter(
                    Activity.user_id == user_id,
                    Activity.activity_date >= m_first,
                    Activity.activity_date <= m_last,
                )
                .scalar()
                or 0
            )
            monthly_trend.append({
                "month_str": month_label,
                "year": m_date.year,
                "month": m_date.month,
                "total_co2": round(float(m_total), 2),
                "target_co2": active_goal.monthly_target if active_goal else None,
                "activity_count": m_count,
            })

        # 9. Recent Daily Emissions (Last 14 Days)
        recent_daily = []
        for i in range(13, -1, -1):
            day_d = today - datetime.timedelta(days=i)
            day_total = (
                db.query(func.sum(Activity.calculated_co2))
                .filter(
                    Activity.user_id == user_id,
                    Activity.activity_date == day_d,
                )
                .scalar()
                or 0.0
            )
            day_count = (
                db.query(func.count(Activity.id))
                .filter(
                    Activity.user_id == user_id,
                    Activity.activity_date == day_d,
                )
                .scalar()
                or 0
            )
            recent_daily.append({
                "date_str": day_d.strftime("%Y-%m-%d"),
                "day_name": day_d.strftime("%a"),
                "total_co2": round(float(day_total), 2),
                "activity_count": day_count,
            })

        # 10. Recent Activities (Last 10)
        recent_activities = (
            db.query(Activity)
            .filter(Activity.user_id == user_id)
            .order_by(Activity.activity_date.desc(), Activity.id.desc())
            .limit(10)
            .all()
        )

        # 11. Sustainability Score
        score_detail = SustainabilityScoreService.calculate_score(
            db=db,
            user_id=user_id,
            current_month_emissions=cur_emissions,
            previous_month_emissions=prev_emissions,
            current_goal=active_goal,
        )

        return {
            "total_monthly_emissions": cur_emissions,
            "previous_month_emissions": prev_emissions,
            "percentage_change": percentage_change,
            "daily_average": daily_average,
            "largest_category": largest_cat_name,
            "largest_category_percentage": largest_cat_pct,
            "total_lifetime_emissions": total_lifetime,
            "total_activities_count": total_activities_count,
            "goal": goal_data,
            "sustainability_score": score_detail,
            "categories_breakdown": categories_breakdown,
            "monthly_trend": monthly_trend,
            "recent_daily_emissions": recent_daily,
            "recent_activities": recent_activities,
        }
