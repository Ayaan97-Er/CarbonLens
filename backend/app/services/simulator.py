from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.carbon_calculator import CarbonCalculationService


class SimulatorService:
    PRESETS = [
        {
            "id": "scenario_commute_car",
            "title": "Reduce Solo Driving by 25%",
            "description": "Replace 1-2 days of solo car commute with public transit, carpooling, or cycling.",
            "activity_type": "Car (Gasoline)",
            "default_quantity": 400.0,
            "unit": "km",
            "default_reduction_pct": 25.0,
        },
        {
            "id": "scenario_home_electricity",
            "title": "Cut Home Power Usage by 20%",
            "description": "Implement smart power strips, LED fixtures, and adjust HVAC set points.",
            "activity_type": "Grid Electricity",
            "default_quantity": 350.0,
            "unit": "kWh",
            "default_reduction_pct": 20.0,
        },
        {
            "id": "scenario_dietary_meat",
            "title": "Swap 30% of Meat Meals to Plant-Based",
            "description": "Shift 10 meals per month from beef/meat to wholesome plant-rich dishes.",
            "activity_type": "Meal (Meat-Heavy / Beef)",
            "default_quantity": 30.0,
            "unit": "meals",
            "default_reduction_pct": 33.3,
        },
        {
            "id": "scenario_heating_gas",
            "title": "Lower Thermostat Gas Consumption by 15%",
            "description": "Improve window insulation and lower nocturnal thermostat temperatures.",
            "activity_type": "Natural Gas (Heating)",
            "default_quantity": 60.0,
            "unit": "m3",
            "default_reduction_pct": 15.0,
        },
        {
            "id": "scenario_flight_reduction",
            "title": "Replace 1 Short Flight with Rail",
            "description": "Choose high-speed electric trains for an intercity round-trip instead of flying.",
            "activity_type": "Flight (Short-Haul < 500km)",
            "default_quantity": 800.0,
            "unit": "km",
            "default_reduction_pct": 50.0,
        },
    ]

    @staticmethod
    def get_presets() -> List[dict]:
        return SimulatorService.PRESETS

    @staticmethod
    def simulate(
        db: Session,
        activity_type: str,
        current_quantity: float,
        reduction_percentage: float,
        category_id: int = None
    ) -> Dict[str, Any]:
        """
        Execute backend What-If simulation calculation.
        """
        factor, unit, _ = CarbonCalculationService.get_factor_for_activity(
            db, activity_type, category_id
        )

        clamped_pct = max(0.0, min(100.0, float(reduction_percentage)))
        projected_quantity = round(current_quantity * (1.0 - (clamped_pct / 100.0)), 2)
        
        current_monthly_co2 = round(current_quantity * factor, 2)
        projected_monthly_co2 = round(projected_quantity * factor, 2)
        monthly_saved_co2 = round(current_monthly_co2 - projected_monthly_co2, 2)
        annual_saved_co2 = round(monthly_saved_co2 * 12.0, 2)

        # Environmental equivalents
        # 1 mature tree absorbs ~21.77 kg CO2 / year
        trees_equiv = round(annual_saved_co2 / 21.77, 1)
        # Average car emits ~0.17 kg CO2 / km
        car_km_equiv = round(annual_saved_co2 / 0.17, 0)

        # Action tip based on activity
        if "Car" in activity_type or "Motorcycle" in activity_type:
            action_tip = f"Reducing {clamped_pct:.0f}% of your monthly driving ({current_quantity - projected_quantity:.1f} {unit}) prevents {annual_saved_co2} kg CO2e annually—equivalent to taking a car off the road for {car_km_equiv:.0f} km!"
        elif "Electricity" in activity_type:
            action_tip = f"Saving {current_quantity - projected_quantity:.1f} {unit} of grid electricity saves {monthly_saved_co2} kg CO2e monthly and lowers your utility bill."
        elif "Meat" in activity_type or "Food" in activity_type:
            action_tip = f"Swapping {current_quantity - projected_quantity:.0f} meals/month to plant-based options has the climate impact of planting {trees_equiv} urban trees."
        elif "Flight" in activity_type:
            action_tip = f"Cutting {current_quantity - projected_quantity:.0f} {unit} of air travel yields {annual_saved_co2} kg CO2e in annual avoidance."
        else:
            action_tip = f"A {clamped_pct:.0f}% reduction saves {annual_saved_co2} kg CO2e each year."

        return {
            "activity_type": activity_type,
            "unit": unit,
            "emission_factor": factor,
            "current_quantity": current_quantity,
            "projected_quantity": projected_quantity,
            "reduction_percentage": clamped_pct,
            "current_monthly_emissions_kg": current_monthly_co2,
            "projected_monthly_emissions_kg": projected_monthly_co2,
            "monthly_emissions_saved_kg": monthly_saved_co2,
            "annual_emissions_saved_kg": annual_saved_co2,
            "trees_equivalent_annual": trees_equiv,
            "car_km_equivalent_annual": car_km_equiv,
            "action_tip": action_tip,
        }
