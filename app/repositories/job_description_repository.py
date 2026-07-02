"""Repository for job description CRUD operations."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription


class JobDescriptionRepository:
    """Data access layer for job descriptions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, title: str, raw_text: str, structured_json: Optional[dict] = None,
                     required_skills: Optional[List[str]] = None,
                     optional_skills: Optional[List[str]] = None,
                     experience_min: Optional[int] = None,
                     experience_max: Optional[int] = None,
                     behavioral_traits: Optional[List[str]] = None) -> JobDescription:
        """Create and persist a new job description."""
        now = datetime.utcnow()
        jd = JobDescription(
            title=title,
            raw_text=raw_text,
            structured_json=structured_json or {},
            required_skills=required_skills or [],
            optional_skills=optional_skills or [],
            experience_min=experience_min,
            experience_max=experience_max,
            behavioral_traits=behavioral_traits or [],
            created_at=now,
            updated_at=now,
        )
        self.session.add(jd)
        await self.session.commit()
        await self.session.refresh(jd)
        return jd

    async def get_by_id(self, jd_id: int) -> Optional[JobDescription]:
        """Retrieve a job description by ID."""
        result = await self.session.execute(
            select(JobDescription).where(JobDescription.id == jd_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Retrieve all job descriptions with pagination."""
        result = await self.session.execute(
            select(JobDescription).offset(skip).limit(limit).order_by(JobDescription.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, jd_id: int, **kwargs) -> Optional[JobDescription]:
        """Update a job description's fields."""
        jd = await self.get_by_id(jd_id)
        if not jd:
            return None
        for key, value in kwargs.items():
            if hasattr(jd, key):
                setattr(jd, key, value)
        jd.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(jd)
        return jd

    async def delete(self, jd_id: int) -> bool:
        """Delete a job description by ID."""
        jd = await self.get_by_id(jd_id)
        if not jd:
            return False
        await self.session.delete(jd)
        await self.session.commit()
        return True