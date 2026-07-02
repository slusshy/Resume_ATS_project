"""Pydantic schemas for predictions."""

from typing import Dict, Optional

from pydantic import BaseModel


class PredictionResponse(BaseModel):
    candidate_id: int
    success_probability: float
    month_1_performance: Optional[str]
    month_3_performance: Optional[str]
    month_6_performance: Optional[str]
    reasoning: Dict[str, str]
