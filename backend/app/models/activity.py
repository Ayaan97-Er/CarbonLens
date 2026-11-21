import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    activity_type = Column(String(100), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    emission_factor = Column(Float, nullable=False)  # Factor recorded at time of activity
    calculated_co2 = Column(Float, nullable=False)  # Total kg CO2e
    activity_date = Column(Date, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="activities")
    category = relationship("Category", back_populates="activities")

    def __repr__(self) -> str:
        return f"<Activity id={self.id} user_id={self.user_id} type='{self.activity_type}' co2={self.calculated_co2}kg>"
