import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.achievement import Achievement, UserAchievement
from app.models.activity import Activity
from app.models.goal import Goal

DEFAULT_ACHIEVEMENTS = [
    {
        "slug": "first_step",
        "name": "First Step",
        "description": "Logged your first carbon-producing or carbon-saving activity.",
        "icon": "footprints",
        "badge_tier": "bronze",
        "requirement_type": "activity_count",
        "requirement_value": 1.0,
    },
    {
        "slug": "consistent_tracker",
        "name": "Consistent Tracker",
        "description": "Logged activities across at least 5 distinct days.",
        "icon": "calendar-check",
        "badge_tier": "silver",
        "requirement_type": "distinct_days",
        "requirement_value": 5.0,
    },
    {
        "slug": "data_devotee",
        "name": "Data Devotee",
        "description": "Logged 25 total activities on your sustainability journey.",
        "icon": "database",
        "badge_tier": "silver",
        "requirement_type": "activity_count",
        "requirement_value": 25.0,
    },
    {
        "slug": "under_budget",
        "name": "Under Budget",
        "description": "Maintained your monthly emissions within your carbon target.",
        "icon": "shield-check",
        "badge_tier": "gold",
        "requirement_type": "under_budget",
        "requirement_value": 1.0,
    },
    {
        "slug": "carbon_cutter",
        "name": "Carbon Cutter",
        "description": "Achieved at least a 10% reduction in monthly emissions compared to previous month.",
        "icon": "trending-down",
        "badge_tier": "gold",
        "requirement_type": "reduction_percentage",
        "requirement_value": 10.0,
    },
    {
        "slug": "green_commuter",
        "name": "Green Commuter",
        "description": "Logged 3 or more zero/low-emission transit activities (bicycle, walking, transit).",
        "icon": "bike",
        "badge_tier": "emerald",
        "requirement_type": "green_transit_count",
        "requirement_value": 3.0,
    },
    {
        "slug": "plant_powered",
        "name": "Plant Powered",
        "description": "Logged 5 or more plant-based or vegetarian meals.",
        "icon": "sprout",
        "badge_tier": "emerald",
        "requirement_type": "plant_meals_count",
        "requirement_value": 5.0,
    },
    {
        "slug": "century_milestone",
        "name": "Century Milestone",
        "description": "Accurately measured and tracked over 100 kg CO2e in emissions.",
        "icon": "award",
        "badge_tier": "gold",
        "requirement_type": "lifetime_co2_tracked",
        "requirement_value": 100.0,
    },
]


class AchievementService:
    @staticmethod
    def ensure_default_achievements(db: Session):
        """Ensure all default achievements exist in DB."""
        for ach_data in DEFAULT_ACHIEVEMENTS:
            existing = db.query(Achievement).filter(Achievement.slug == ach_data["slug"]).first()
            if not existing:
                achievement = Achievement(
                    slug=ach_data["slug"],
                    name=ach_data["name"],
                    description=ach_data["description"],
                    icon=ach_data["icon"],
                    badge_tier=ach_data["badge_tier"],
                    requirement_type=ach_data["requirement_type"],
                    requirement_value=ach_data["requirement_value"],
                )
                db.add(achievement)
        db.commit()

    @staticmethod
    def evaluate_user_achievements(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Evaluate user progress and auto-unlock newly qualified achievements.
        Returns list of all achievements with unlock and progress status.
        """
        AchievementService.ensure_default_achievements(db)

        # Gather user metrics
        today = datetime.date.today()
        month_start = datetime.date(today.year, today.month, 1)

        total_activities = db.query(func.count(Activity.id)).filter(Activity.user_id == user_id).scalar() or 0
        distinct_days = db.query(func.count(func.distinct(Activity.activity_date))).filter(Activity.user_id == user_id).scalar() or 0
        total_co2 = db.query(func.sum(Activity.calculated_co2)).filter(Activity.user_id == user_id).scalar() or 0.0

        # Transit count
        green_transit_count = (
            db.query(func.count(Activity.id))
            .filter(
                Activity.user_id == user_id,
                (
                    Activity.activity_type.ilike("%Bicycle%")
                    | Activity.activity_type.ilike("%Walking%")
                    | Activity.activity_type.ilike("%Train%")
                    | Activity.activity_type.ilike("%Metro%")
                    | Activity.activity_type.ilike("%Transit%")
                    | Activity.activity_type.ilike("%Bus%")
                ),
            )
            .scalar()
            or 0
        )

        # Plant meals count
        plant_meals_count = (
            db.query(func.count(Activity.id))
            .filter(
                Activity.user_id == user_id,
                (
                    Activity.activity_type.ilike("%Vegan%")
                    | Activity.activity_type.ilike("%Vegetarian%")
                ),
            )
            .scalar()
            or 0
        )

        # Under budget check
        active_goal = db.query(Goal).filter(Goal.user_id == user_id, Goal.is_active == True).first()
        cur_month_co2 = (
            db.query(func.sum(Activity.calculated_co2))
            .filter(
                Activity.user_id == user_id,
                Activity.activity_date >= month_start,
            )
            .scalar()
            or 0.0
        )

        is_under_budget = 1.0 if (active_goal and cur_month_co2 > 0 and cur_month_co2 <= active_goal.monthly_target) else 0.0

        # MoM reduction check
        if today.month == 1:
            prev_first = datetime.date(today.year - 1, 12, 1)
            prev_last = datetime.date(today.year - 1, 12, 31)
        else:
            prev_first = datetime.date(today.year, today.month - 1, 1)
            prev_last = datetime.date(today.year, today.month, 1) - datetime.timedelta(days=1)

        prev_month_co2 = (
            db.query(func.sum(Activity.calculated_co2))
            .filter(
                Activity.user_id == user_id,
                Activity.activity_date >= prev_first,
                Activity.activity_date <= prev_last,
            )
            .scalar()
            or 0.0
        )

        reduction_pct = 0.0
        if prev_month_co2 > 0 and cur_month_co2 > 0:
            reduction_pct = max(0.0, ((prev_month_co2 - cur_month_co2) / prev_month_co2) * 100)

        # Fetch all achievements and unlocked records
        all_achievements = db.query(Achievement).all()
        unlocked_records = {
            ua.achievement_id: ua.unlocked_at
            for ua in db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()
        }

        results = []
        newly_unlocked = False

        for ach in all_achievements:
            req_type = ach.requirement_type
            req_val = ach.requirement_value
            current_val = 0.0

            if req_type == "activity_count":
                current_val = float(total_activities)
            elif req_type == "distinct_days":
                current_val = float(distinct_days)
            elif req_type == "under_budget":
                current_val = float(is_under_budget)
            elif req_type == "reduction_percentage":
                current_val = float(reduction_pct)
            elif req_type == "green_transit_count":
                current_val = float(green_transit_count)
            elif req_type == "plant_meals_count":
                current_val = float(plant_meals_count)
            elif req_type == "lifetime_co2_tracked":
                current_val = float(total_co2)

            is_qualifying = current_val >= req_val
            progress_pct = min(100.0, round((current_val / req_val) * 100.0, 1)) if req_val > 0 else 0.0

            unlocked_at = unlocked_records.get(ach.id)
            if is_qualifying and not unlocked_at:
                # Auto-unlock
                new_ua = UserAchievement(
                    user_id=user_id,
                    achievement_id=ach.id,
                    unlocked_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.add(new_ua)
                unlocked_at = new_ua.unlocked_at
                newly_unlocked = True

            results.append({
                "id": ach.id,
                "slug": ach.slug,
                "name": ach.name,
                "description": ach.description,
                "icon": ach.icon,
                "badge_tier": ach.badge_tier,
                "requirement_type": ach.requirement_type,
                "requirement_value": ach.requirement_value,
                "is_unlocked": unlocked_at is not None,
                "unlocked_at": unlocked_at,
                "progress_percentage": 100.0 if unlocked_at else progress_pct,
                "current_progress": round(current_val, 1),
            })

        if newly_unlocked:
            db.commit()

        return results
