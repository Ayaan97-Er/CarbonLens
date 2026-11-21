import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.activity import Activity
from app.models.category import Category


class RecommendationEngine:
    @staticmethod
    def generate_recommendations(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Deterministic rule-based recommendation engine based on user activity profile.
        """
        today = datetime.date.today()
        month_start = datetime.date(today.year, today.month, 1)

        # Query user category totals for past 60 days to have strong statistical signal
        cutoff_date = today - datetime.timedelta(days=60)
        cat_stats = (
            db.query(
                Category.name,
                Category.icon,
                func.sum(Activity.calculated_co2).label("total_co2"),
                func.count(Activity.id).label("act_count"),
            )
            .join(Activity, Activity.category_id == Category.id)
            .filter(
                Activity.user_id == user_id,
                Activity.activity_date >= cutoff_date,
            )
            .group_by(Category.name, Category.icon)
            .order_by(desc("total_co2"))
            .all()
        )

        recommendations: List[dict] = []
        total_co2 = sum([c.total_co2 for c in cat_stats]) if cat_stats else 0.0

        dominant_cat = cat_stats[0].name if cat_stats else None

        # Rule 1: Transportation dominant (> 35% or > 80 kg)
        trans_stat = next((c for c in cat_stats if "Transportation" in c.name), None)
        if trans_stat and (trans_stat.total_co2 > 50 or (total_co2 > 0 and trans_stat.total_co2 / total_co2 > 0.35)):
            monthly_trans = round(float(trans_stat.total_co2) / 2, 1)
            potential_save = round(monthly_trans * 0.30, 1)  # 30% reduction via transit/cycling
            recommendations.append({
                "id": "rec_trans_commute",
                "category_name": "Transportation",
                "category_icon": "car",
                "title": "Shift 2 Commutes / Week to Public Transit or Cycling",
                "description": f"Transportation represents {round((trans_stat.total_co2 / (total_co2 or 1))*100, 0)}% of your recent footprint ({round(trans_stat.total_co2, 1)} kg CO2e). Replacing 2 weekly solo car trips with train, bus, or cycling cuts emissions drastically.",
                "impact_level": "high",
                "potential_monthly_savings_kg": potential_save,
                "actionable_step": "Try taking the train or riding an e-bike for your mid-week commute.",
                "relevance_reason": "High transportation share in your recent logs",
            })

        # Rule 2: Electricity consumption
        elec_stat = next((c for c in cat_stats if "Electricity" in c.name), None)
        if elec_stat and elec_stat.total_co2 > 40:
            potential_save = round((float(elec_stat.total_co2) / 2) * 0.20, 1)  # 20% efficiency
            recommendations.append({
                "id": "rec_elec_efficiency",
                "category_name": "Electricity",
                "category_icon": "zap",
                "title": "Optimize Home Temperature & Vampire Power",
                "description": "Grid electricity contributes substantially to your footprint. Lowering thermostat by 1°C in winter / raising 1°C in summer plus using smart strips reduces grid draw by 15-20%.",
                "impact_level": "medium",
                "potential_monthly_savings_kg": potential_save,
                "actionable_step": "Install smart plugs on home entertainment and workstation equipment.",
                "relevance_reason": "Consistent grid electricity consumption recorded",
            })

        # Rule 3: Food & Meat-Heavy Diet
        food_stat = next((c for c in cat_stats if "Food" in c.name), None)
        # Check if user logged meat-heavy meals
        meat_count = (
            db.query(func.count(Activity.id))
            .filter(
                Activity.user_id == user_id,
                Activity.activity_date >= cutoff_date,
                Activity.activity_type.ilike("%Meat%"),
            )
            .scalar()
            or 0
        )
        if meat_count >= 3 or (food_stat and food_stat.total_co2 > 30):
            potential_save = round(meat_count * 2.4 * 2, 1)  # Saving ~2.4 kg per swapped meal
            potential_save = max(15.0, min(80.0, potential_save))
            recommendations.append({
                "id": "rec_food_plant_shift",
                "category_name": "Food & Diet",
                "category_icon": "utensils",
                "title": "Embrace 'Meatless Mondays' / Plant-Forward Dining",
                "description": "Red meat has an emission factor of ~3.3 kg CO2e per meal compared to ~0.5 kg for plant-based alternatives. Swapping 2-3 meat meals a week yields immediate sustainability gains.",
                "impact_level": "medium",
                "potential_monthly_savings_kg": potential_save,
                "actionable_step": "Try exploring delicious lentil, tofu, or Mediterranean grain bowls twice a week.",
                "relevance_reason": f"Logged {meat_count} high-intensity meals in the last 60 days",
            })

        # Rule 4: Flights / Aviation
        flight_stat = next((c for c in cat_stats if "Flight" in c.name), None)
        if flight_stat and flight_stat.total_co2 > 50:
            potential_save = round(float(flight_stat.total_co2) * 0.4, 1)
            recommendations.append({
                "id": "rec_flight_alternatives",
                "category_name": "Flights",
                "category_icon": "plane",
                "title": "Choose High-Speed Rail for Short-Haul Routes (<500 km)",
                "description": "Short-haul flights produce nearly 6x the CO2e per passenger-kilometer compared to electrified rail systems. Opting for trains on regional corridors significantly curtails footprint.",
                "impact_level": "high",
                "potential_monthly_savings_kg": potential_save,
                "actionable_step": "Check train schedules for trips under 4 hours before booking short flights.",
                "relevance_reason": "High-impact flight activity detected",
            })

        # Rule 5: Natural Gas / Heating
        gas_stat = next((c for c in cat_stats if "Natural Gas" in c.name), None)
        if gas_stat and gas_stat.total_co2 > 40:
            potential_save = round((float(gas_stat.total_co2) / 2) * 0.15, 1)
            recommendations.append({
                "id": "rec_gas_weatherization",
                "category_name": "Natural Gas",
                "category_icon": "flame",
                "title": "Draft-Proof Doors and Windows",
                "description": "Natural gas combustion for space and water heating generates ~2.03 kg CO2e/m³. Sealing air leaks and insulating hot water pipes decreases heating load by 12-18%.",
                "impact_level": "medium",
                "potential_monthly_savings_kg": potential_save,
                "actionable_step": "Apply self-adhesive weatherstripping to exterior doors and window frames.",
                "relevance_reason": "Natural gas heating identified as an ongoing emission contributor",
            })

        # Rule 6: Shopping & Consumer Goods
        shop_stat = next((c for c in cat_stats if "Shopping" in c.name), None)
        if shop_stat and shop_stat.total_co2 > 25:
            potential_save = round((float(shop_stat.total_co2) / 2) * 0.25, 1)
            recommendations.append({
                "id": "rec_shopping_circular",
                "category_name": "Shopping",
                "category_icon": "shopping-bag",
                "title": "Prioritize Circular & Refurbished Goods",
                "description": "Manufacturing embedded emissions account for the majority of consumer goods lifecycles. Choosing refurbished tech and high-quality durable apparel prevents upstream manufacturing footprints.",
                "impact_level": "low",
                "potential_monthly_savings_kg": potential_save,
                "actionable_step": "Adopt a 48-hour pause rule before non-essential purchases.",
                "relevance_reason": "Consumer shopping footprint logged",
            })

        # Fallback general recommendations if user has few activities
        if len(recommendations) < 2:
            recommendations.append({
                "id": "rec_general_habits",
                "category_name": "Lifestyle",
                "category_icon": "compass",
                "title": "Establish a Daily Carbon Logging Habit",
                "description": "Research shows that consistent awareness and daily logging alone correlates with a 10-15% voluntary carbon reduction over a 3-month period.",
                "impact_level": "low",
                "potential_monthly_savings_kg": 18.5,
                "actionable_step": "Log your daily transport and main meals each evening.",
                "relevance_reason": "Baseline habit building for new CarbonLens members",
            })
            recommendations.append({
                "id": "rec_general_transport",
                "category_name": "Transportation",
                "category_icon": "bike",
                "title": "Integrate Active Mobility for Local Errands",
                "description": "Nearly 40% of urban car trips are under 3 kilometers. Walking or cycling for errands produces zero direct emissions while improving cardiovascular health.",
                "impact_level": "medium",
                "potential_monthly_savings_kg": 24.0,
                "actionable_step": "Walk or bike for any errand within 1.5 km this week.",
                "relevance_reason": "Universal high-yield carbon reduction strategy",
            })

        total_potential_monthly = round(sum(r["potential_monthly_savings_kg"] for r in recommendations), 1)
        total_potential_annual = round(total_potential_monthly * 12, 1)

        return {
            "recommendations": recommendations,
            "total_potential_monthly_savings_kg": total_potential_monthly,
            "total_potential_annual_savings_kg": total_potential_annual,
            "dominant_category": dominant_cat,
        }
