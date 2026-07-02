"""Hiring success prediction model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Float, String

from app.models import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    success_probability = Column(Float, nullable=False)
    month_1_performance = Column(String, nullable=True)
    month_3_performance = Column(String, nullable=True)
    month_6_performance = Column(String, nullable=True)
    reasoning = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False)
