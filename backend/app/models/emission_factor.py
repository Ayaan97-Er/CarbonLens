import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    activity_type = Column(String(100), nullable=False, index=True)  # e.g., "Car (Gasoline)", "Electricity (Grid)"
    unit = Column(String(50), nullable=False)  # e.g., "km", "miles", "kWh", "m3", "meals", "USD"
    factor = Column(Float, nullable=False)  # kg CO2e per unit
    source = Column(String(255), nullable=True)  # e.g. "EPA 2024", "DEFRA 2024", "IPCC AR6"
    version = Column(String(50), default="1.0", nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    category = relationship("Category", back_populates="emission_factors")

    def __repr__(self) -> str:
        return f"<EmissionFactor {self.activity_type} ({self.factor} kg CO2e/{self.unit})>"
