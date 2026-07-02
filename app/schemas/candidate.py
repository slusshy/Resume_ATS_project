"""Pydantic schemas for candidate profiles."""

from typing import List, Optional

from pydantic import BaseModel


class CandidateCreate(BaseModel):
    name: str
    profile_text: str


class CandidateProfileResult(BaseModel):
    skills: List[str]
    experience_years: Optional[float]
    projects: List[str]
    certifications: List[str]
    profile_json: dict
