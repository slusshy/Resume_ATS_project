"""Pydantic schemas for analysis output."""

from typing import Dict, List, Optional

from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    job_description_id: int
    candidate_ids: Optional[List[int]] = None  # Optional - if not provided, analyze all candidates


class AnalysisResult(BaseModel):
    technical_fit_score: float
    behavioral_fit_score: float
    learning_agility_score: float
    stability_score: float
    growth_potential_score: float
    overall_score: float
    explanations: Dict[str, str]
