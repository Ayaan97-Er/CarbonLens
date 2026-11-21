from typing import Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.emission_factor import EmissionFactor
from app.models.category import Category


# Fallback default factor table if database is initializing or custom type used
DEFAULT_FACTORS = {
    # Transportation (kg CO2e / km)
    "Car (Gasoline)": {"factor": 0.192, "unit": "km", "category": "Transportation", "source": "EPA 2024"},
    "Car (Diesel)": {"factor": 0.171, "unit": "km", "category": "Transportation", "source": "EPA 2024"},
    "Car (Electric / EV)": {"factor": 0.053, "unit": "km", "category": "Transportation", "source": "DEFRA 2024"},
    "Car (Hybrid)": {"factor": 0.109, "unit": "km", "category": "Transportation", "source": "EPA 2024"},
    "Motorcycle": {"factor": 0.113, "unit": "km", "category": "Transportation", "source": "DEFRA 2024"},
    "Bus (Transit)": {"factor": 0.089, "unit": "km", "category": "Transportation", "source": "DEFRA 2024"},
    "Train / Rail": {"factor": 0.041, "unit": "km", "category": "Transportation", "source": "DEFRA 2024"},
    "Subway / Metro": {"factor": 0.035, "unit": "km", "category": "Transportation", "source": "DEFRA 2024"},
    "Bicycle": {"factor": 0.0, "unit": "km", "category": "Transportation", "source": "Zero Direct Emissions"},
    "Walking": {"factor": 0.0, "unit": "km", "category": "Transportation", "source": "Zero Direct Emissions"},

    # Flights (kg CO2e / km or trip)
    "Flight (Short-Haul < 500km)": {"factor": 0.255, "unit": "km", "category": "Flights", "source": "DEFRA 2024"},
    "Flight (Medium-Haul 500-3700km)": {"factor": 0.156, "unit": "km", "category": "Flights", "source": "DEFRA 2024"},
    "Flight (Long-Haul > 3700km)": {"factor": 0.150, "unit": "km", "category": "Flights", "source": "DEFRA 2024"},

    # Electricity (kg CO2e / kWh)
    "Grid Electricity": {"factor": 0.385, "unit": "kWh", "category": "Electricity", "source": "EPA eGRID 2024"},
    "Renewable Electricity (Solar/Wind)": {"factor": 0.015, "unit": "kWh", "category": "Electricity", "source": "NREL Lifecycle"},

    # Natural Gas (kg CO2e / m3)
    "Natural Gas (Heating)": {"factor": 2.03, "unit": "m3", "category": "Natural Gas", "source": "DEFRA 2024"},
    "Propane / LPG": {"factor": 1.51, "unit": "liter", "category": "Natural Gas", "source": "EPA 2024"},

    # Food & Diet (kg CO2e / meal or day)
    "Meal (Meat-Heavy / Beef)": {"factor": 3.30, "unit": "meals", "category": "Food", "source": "Poore & Nemecek Science"},
    "Meal (Mixed / Average)": {"factor": 1.70, "unit": "meals", "category": "Food", "source": "Poore & Nemecek Science"},
    "Meal (Vegetarian)": {"factor": 0.90, "unit": "meals", "category": "Food", "source": "Poore & Nemecek Science"},
    "Meal (Vegan / Plant-Based)": {"factor": 0.50, "unit": "meals", "category": "Food", "source": "Poore & Nemecek Science"},

    # Shopping & Goods (kg CO2e / USD spent or item)
    "Clothing / Apparel Purchase": {"factor": 0.45, "unit": "USD", "category": "Shopping", "source": "EEIO Model 2024"},
    "Electronics / Tech Device": {"factor": 0.60, "unit": "USD", "category": "Shopping", "source": "EEIO Model 2024"},
    "General Goods & Packaging": {"factor": 0.35, "unit": "USD", "category": "Shopping", "source": "EEIO Model 2024"},
}


class CarbonCalculationService:
    @staticmethod
    def get_factor_for_activity(
        db: Session,
        activity_type: str,
        category_id: Optional[int] = None
    ) -> Tuple[float, str, Optional[str]]:
        """
        Look up the emission factor, unit, and source from DB or fallback table.
        Returns: (factor: float, unit: str, source: str)
        """
        query = db.query(EmissionFactor).filter(
            EmissionFactor.activity_type == activity_type,
            EmissionFactor.is_active == True
        )
        if category_id:
            query = query.filter(EmissionFactor.category_id == category_id)

        factor_obj = query.first()

        if factor_obj:
            return factor_obj.factor, factor_obj.unit, factor_obj.source

        # Case-insensitive or partial match fallback in DB
        factor_obj = db.query(EmissionFactor).filter(
            EmissionFactor.activity_type.ilike(f"%{activity_type}%"),
            EmissionFactor.is_active == True
        ).first()

        if factor_obj:
            return factor_obj.factor, factor_obj.unit, factor_obj.source

        # Default fallback dictionary
        if activity_type in DEFAULT_FACTORS:
            meta = DEFAULT_FACTORS[activity_type]
            return meta["factor"], meta["unit"], meta["source"]

        # Default minimal fallback
        return 0.15, "unit", "Estimated average"

    @staticmethod
    def calculate_co2(
        quantity: float,
        emission_factor: float
    ) -> float:
        """
        Calculate total estimated kg CO2e.
        Formula: quantity * emission_factor
        Rounds to 3 decimal places for precision.
        """
        if quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activity quantity must be non-negative"
            )
        calculated = quantity * emission_factor
        return round(calculated, 3)

    @staticmethod
    def preview_calculation(
        db: Session,
        activity_type: str,
        quantity: float,
        category_id: Optional[int] = None,
        custom_factor: Optional[float] = None
    ) -> dict:
        """Calculate a live preview without persisting."""
        if custom_factor is not None:
            factor = custom_factor
            unit = "unit"
            source = "User specified"
        else:
            factor, unit, source = CarbonCalculationService.get_factor_for_activity(
                db, activity_type, category_id
            )
        
        calculated_co2 = CarbonCalculationService.calculate_co2(quantity, factor)
        return {
            "activity_type": activity_type,
            "quantity": quantity,
            "unit": unit,
            "emission_factor": factor,
            "factor_source": source,
            "calculated_co2_kg": calculated_co2,
        }
