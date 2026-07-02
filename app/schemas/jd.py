"""Pydantic schemas for job descriptions."""

from typing import List, Optional

from pydantic import BaseModel


class JobDescriptionCreate(BaseModel):
    title: str
    description: str


class JobDescriptionParseResult(BaseModel):
    required_skills: List[str]
    optional_skills: List[str]
    experience_min: Optional[int]
    experience_max: Optional[int]
    behavioral_traits: List[str]
    structured_json: dict
