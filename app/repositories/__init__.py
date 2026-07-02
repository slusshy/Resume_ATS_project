"""Repository layer for database access."""

from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.ranking_repository import RankingRepository
from app.repositories.prediction_repository import PredictionRepository

__all__ = [
    "CandidateRepository",
    "JobDescriptionRepository",
    "RankingRepository",
    "PredictionRepository",
]