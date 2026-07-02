"""Repository for hiring prediction CRUD operations."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction


class PredictionRepository:
    """Data access layer for hiring success predictions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, candidate_id: int, job_description_id: int,
                     success_probability: float,
                     month_1_performance: Optional[str] = None,
                     month_3_performance: Optional[str] = None,
                     month_6_performance: Optional[str] = None,
                     reasoning: Optional[Dict[str, str]] = None) -> Prediction:
        """Create and persist a new prediction record."""
        prediction = Prediction(
            candidate_id=candidate_id,
            job_description_id=job_description_id,
            success_probability=success_probability,
            month_1_performance=month_1_performance,
            month_3_performance=month_3_performance,
            month_6_performance=month_6_performance,
            reasoning=reasoning or {},
            created_at=datetime.utcnow(),
        )
        self.session.add(prediction)
        await self.session.commit()
        await self.session.refresh(prediction)
        return prediction

    async def get_by_id(self, prediction_id: int) -> Optional[Prediction]:
        """Retrieve a prediction by ID."""
        result = await self.session.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        return result.scalar_one_or_none()

    async def get_for_candidate(self, candidate_id: int,
                                 job_description_id: Optional[int] = None) -> List[Prediction]:
        """Retrieve predictions for a candidate, optionally filtered by job."""
        query = select(Prediction).where(Prediction.candidate_id == candidate_id)
        if job_description_id is not None:
            query = query.where(Prediction.job_description_id == job_description_id)
        result = await self.session.execute(query.order_by(Prediction.created_at.desc()))
        return list(result.scalars().all())

    async def get_for_job(self, job_description_id: int,
                          skip: int = 0, limit: int = 100) -> List[Prediction]:
        """Retrieve all predictions for a job description."""
        result = await self.session.execute(
            select(Prediction)
            .where(Prediction.job_description_id == job_description_id)
            .order_by(Prediction.success_probability.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def delete_for_job(self, job_description_id: int) -> int:
        """Delete all predictions for a job. Returns count deleted."""
        predictions = await self.get_for_job(job_description_id, limit=10000)
        count = len(predictions)
        for p in predictions:
            await self.session.delete(p)
        await self.session.commit()
        return count