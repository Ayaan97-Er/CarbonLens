import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ActivityBase(BaseModel):
    category_id: int
    activity_type: str = Field(..., min_length=1, max_length=100)
    quantity: float = Field(..., gt=0, description="Numerical quantity of activity")
    unit: str = Field(..., min_length=1, max_length=50)
    activity_date: datetime.date
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("activity_date")
    @classmethod
    def validate_date(cls, v: datetime.date) -> datetime.date:
        today = datetime.date.today()
        # Allow logging activities up to 1 year back and not more than 1 day in the future
        if v > today + datetime.timedelta(days=1):
            raise ValueError("Activity date cannot be in the future")
        return v


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    category_id: Optional[int] = None
    activity_type: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    activity_date: Optional[datetime.date] = None
    notes: Optional[str] = Field(None, max_length=1000)


class ActivityCategoryOut(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None

    class Config:
        from_attributes = True


class ActivityOut(BaseModel):
    id: int
    user_id: int
    category_id: Optional[int] = None
    activity_type: str
    quantity: float
    unit: str
    emission_factor: float
    calculated_co2: float  # kg CO2e
    activity_date: datetime.date
    notes: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    category: Optional[ActivityCategoryOut] = None

    class Config:
        from_attributes = True


class PaginatedActivities(BaseModel):
    items: List[ActivityOut]
    total: int
    page: int
    page_size: int
    total_pages: int
    total_emissions_kg: float


class ActivityCalculationPreview(BaseModel):
    activity_type: str
    quantity: float
    unit: str
    emission_factor: float
    factor_source: Optional[str]
    calculated_co2_kg: float
