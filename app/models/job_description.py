"""Job description data model."""

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text

from app.models import Base


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    structured_json = Column(JSON, nullable=True)
    required_skills = Column(JSON, nullable=True)
    optional_skills = Column(JSON, nullable=True)
    experience_min = Column(Integer, nullable=True)
    experience_max = Column(Integer, nullable=True)
    behavioral_traits = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
