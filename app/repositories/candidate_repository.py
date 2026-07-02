"""Repository for candidate CRUD operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_profile import CandidateProfile


class CandidateRepository:
    """Data access layer for candidate profiles."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, raw_profile: str, profile_json: Optional[Dict[str, Any]] = None,
                     skills: Optional[List[str]] = None,
                     experience_years: Optional[int] = None,
                     languages: Optional[List[str]] = None,
                     education: Optional[str] = None,
                     certifications: Optional[List[str]] = None,
                     projects: Optional[List[Dict[str, Any]]] = None,
                     summary: Optional[str] = None) -> CandidateProfile:
        """Create and persist a new candidate profile."""
        now = datetime.utcnow()
        candidate = CandidateProfile(
            name=name,
            raw_profile=raw_profile,
            profile_json=profile_json or {},
            skills=skills or [],
            experience_years=experience_years,
            languages=languages or [],
            education=education,
            certifications=certifications or [],
            projects=projects or [],
            summary=summary,
            created_at=now,
            updated_at=now,
        )
        self.session.add(candidate)
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def get_by_id(self, candidate_id: int) -> Optional[CandidateProfile]:
        """Retrieve a candidate by ID."""
        result = await self.session.execute(
            select(CandidateProfile).where(CandidateProfile.id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[CandidateProfile]:
        """Retrieve all candidates with pagination."""
        result = await self.session.execute(
            select(CandidateProfile).offset(skip).limit(limit).order_by(CandidateProfile.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_ids(self, candidate_ids: List[int]) -> List[CandidateProfile]:
        """Retrieve multiple candidates by IDs."""
        result = await self.session.execute(
            select(CandidateProfile).where(CandidateProfile.id.in_(candidate_ids))
        )
        return list(result.scalars().all())

    async def update(self, candidate_id: int, **kwargs) -> Optional[CandidateProfile]:
        """Update a candidate's fields."""
        candidate = await self.get_by_id(candidate_id)
        if not candidate:
            return None
        for key, value in kwargs.items():
            if hasattr(candidate, key):
                setattr(candidate, key, value)
        candidate.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def delete(self, candidate_id: int) -> bool:
        """Delete a candidate by ID."""
        candidate = await self.get_by_id(candidate_id)
        if not candidate:
            return False
        await self.session.delete(candidate)
        await self.session.commit()
        return True

    async def count(self) -> int:
        """Return total candidate count."""
        result = await self.session.execute(select(func.count(CandidateProfile.id)))
        return int(result.scalar_one())
