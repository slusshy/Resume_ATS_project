"""Repository for ranking CRUD operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ranking import Ranking


class RankingRepository:
    """Data access layer for candidate rankings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, candidate_id: int, job_description_id: int,
                     technical_fit_score: float, behavioral_fit_score: float,
                     learning_agility_score: float, stability_score: float,
                     growth_potential_score: float, overall_score: float,
                     explanations: Optional[Dict[str, str]] = None,
                     gemini_fit_score: Optional[float] = None,
                     gemini_reasoning: Optional[str] = None) -> Ranking:
        """Create and persist a new ranking record."""
        ranking = Ranking(
            candidate_id=candidate_id,
            job_description_id=job_description_id,
            technical_fit_score=technical_fit_score,
            behavioral_fit_score=behavioral_fit_score,
            learning_agility_score=learning_agility_score,
            stability_score=stability_score,
            growth_potential_score=growth_potential_score,
            overall_score=overall_score,
            explanations=explanations or {},
            gemini_fit_score=gemini_fit_score,
            gemini_reasoning=gemini_reasoning,
            created_at=datetime.utcnow(),
        )
        self.session.add(ranking)
        await self.session.commit()
        await self.session.refresh(ranking)
        return ranking

    async def bulk_create(self, rankings: List[Dict[str, Any]]) -> List[Ranking]:
        """Create multiple ranking records in bulk."""
        now = datetime.utcnow()
        objects = []
        for r in rankings:
            obj = Ranking(
                candidate_id=r["candidate_id"],
                job_description_id=r["job_description_id"],
                technical_fit_score=r["technical_fit_score"],
                behavioral_fit_score=r["behavioral_fit_score"],
                learning_agility_score=r["learning_agility_score"],
                stability_score=r["stability_score"],
                growth_potential_score=r["growth_potential_score"],
                overall_score=r["overall_score"],
                explanations=r.get("explanations", {}),
                gemini_fit_score=r.get("gemini_fit_score"),
                gemini_reasoning=r.get("gemini_reasoning"),
                created_at=now,
            )
            self.session.add(obj)
            objects.append(obj)
        await self.session.commit()
        for obj in objects:
            await self.session.refresh(obj)
        return objects

    async def get_by_id(self, ranking_id: int) -> Optional[Ranking]:
        """Retrieve a ranking by ID."""
        result = await self.session.execute(
            select(Ranking).where(Ranking.id == ranking_id)
        )
        return result.scalar_one_or_none()

    async def get_for_job(self, job_description_id: int,
                          skip: int = 0, limit: int = 100) -> List[Ranking]:
        """Retrieve all rankings for a specific job description, ordered by score descending."""
        result = await self.session.execute(
            select(Ranking)
            .where(Ranking.job_description_id == job_description_id)
            .order_by(Ranking.overall_score.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_for_candidate_and_job(self, candidate_id: int,
                                         job_description_id: int) -> Optional[Ranking]:
        """Retrieve a specific ranking by candidate and job."""
        result = await self.session.execute(
            select(Ranking).where(
                Ranking.candidate_id == candidate_id,
                Ranking.job_description_id == job_description_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_for_job(self, job_description_id: int) -> int:
        """Delete all rankings for a job description. Returns count deleted."""
        rankings = await self.get_for_job(job_description_id, limit=10000)
        count = len(rankings)
        for r in rankings:
            await self.session.delete(r)
        await self.session.commit()
        return count