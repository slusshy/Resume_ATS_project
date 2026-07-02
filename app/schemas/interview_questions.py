"""Pydantic schemas for generated interview questions."""

from typing import List

from pydantic import BaseModel


class InterviewQuestionsResponse(BaseModel):
    technical_questions: List[str]
    behavioral_questions: List[str]
    leadership_questions: List[str]
    risk_validation_questions: List[str]
