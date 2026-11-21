from typing import List, Optional
from pydantic import BaseModel, Field


class EmissionFactorBase(BaseModel):
    activity_type: str
    unit: str
    factor: float = Field(..., description="kg CO2e per unit")
    source: Optional[str] = None
    version: str = "1.0"
    description: Optional[str] = None
    is_active: bool = True


class EmissionFactorCreate(EmissionFactorBase):
    category_id: int


class EmissionFactorOut(EmissionFactorBase):
    id: int
    category_id: int

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    id: int

    class Config:
        from_attributes = True


class CategoryDetailOut(CategoryOut):
    emission_factors: List[EmissionFactorOut] = []

    class Config:
        from_attributes = True
