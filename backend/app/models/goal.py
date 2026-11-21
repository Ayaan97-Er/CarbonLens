import datetime
from sqlalchemy import Column, Integer, Float, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    monthly_target = Column(Float, nullable=False)  # in kg CO2e
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="goals")

    def __repr__(self) -> str:
        return f"<Goal id={self.id} user_id={self.user_id} target={self.monthly_target}kg>"
