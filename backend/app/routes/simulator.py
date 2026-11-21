from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.simulator import SimulatorRequest, SimulatorResult, QuickScenarioPreset
from app.services.simulator import SimulatorService

router = APIRouter(prefix="/simulator", tags=["What-If Simulator"])


@router.get("/presets", response_model=List[QuickScenarioPreset])
def get_simulation_presets():
    """Retrieve preconfigured high-impact What-If reduction scenarios."""
    return SimulatorService.get_presets()


@router.post("/calculate", response_model=SimulatorResult)
def calculate_simulation(
    sim_in: SimulatorRequest,
    db: Session = Depends(get_db),
):
    """
    Simulate carbon footprint reduction. Calculates baseline emissions,
    projected emissions, monthly & annual savings, tree absorption equivalents,
    and avoided driving km.
    """
    result = SimulatorService.simulate(
        db=db,
        activity_type=sim_in.activity_type,
        current_quantity=sim_in.current_quantity,
        reduction_percentage=sim_in.reduction_percentage,
        category_id=sim_in.category_id,
    )
    return result
