"""Candidate ranking model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Float, String

from app.models import Base


class Ranking(Base):
    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    technical_fit_score = Column(Float, nullable=False)
    behavioral_fit_score = Column(Float, nullable=False)
    learning_agility_score = Column(Float, nullable=False)
    stability_score = Column(Float, nullable=False)
    growth_potential_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    explanations = Column(JSON, nullable=True)
    gemini_fit_score = Column(Float, nullable=True)
    gemini_reasoning = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
