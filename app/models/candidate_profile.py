"""Candidate profile data model."""

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text

from app.models import Base


class CandidateProfile(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    raw_profile = Column(Text, nullable=False)
    profile_json = Column(JSON, nullable=True)
    skills = Column(JSON, nullable=True)
    experience_years = Column(Integer, nullable=True)
    languages = Column(JSON, nullable=True)
    education = Column(String, nullable=True)
    certifications = Column(JSON, nullable=True)
    projects = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
