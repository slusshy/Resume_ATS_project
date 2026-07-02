"""Pydantic schemas for rankings."""

from typing import Dict

from pydantic import BaseModel


class RankingResponse(BaseModel):
    candidate_id: int
    technical_fit_score: float
    behavioral_fit_score: float
    learning_agility_score: float
    stability_score: float
    growth_potential_score: float
    overall_score: float
    explanations: Dict[str, str]
