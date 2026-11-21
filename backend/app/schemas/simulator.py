from typing import List, Optional
from pydantic import BaseModel, Field


class SimulatorRequest(BaseModel):
    category_id: Optional[int] = None
    activity_type: str = Field(..., description="Activity type to simulate")
    current_quantity: float = Field(..., gt=0, description="Monthly baseline quantity")
    reduction_percentage: float = Field(..., ge=1, le=100, description="Percentage to reduce (1-100%)")


class SimulatorResult(BaseModel):
    activity_type: str
    unit: str
    emission_factor: float
    current_quantity: float
    projected_quantity: float
    reduction_percentage: float
    current_monthly_emissions_kg: float
    projected_monthly_emissions_kg: float
    monthly_emissions_saved_kg: float
    annual_emissions_saved_kg: float
    trees_equivalent_annual: float  # ~21.77 kg CO2 absorbed per mature tree per year
    car_km_equivalent_annual: float  # equivalent km avoided in standard gasoline car (~0.17 kg/km)
    action_tip: str


class QuickScenarioPreset(BaseModel):
    id: str
    title: str
    description: str
    activity_type: str
    default_quantity: float
    unit: str
    default_reduction_pct: float
