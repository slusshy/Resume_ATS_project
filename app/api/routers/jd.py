"""Job description API router."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.repositories.job_description_repository import JobDescriptionRepository
from app.schemas.jd import JobDescriptionCreate
from app.services.jd_intent import JobIntentParser

router = APIRouter()
_jd_parser = JobIntentParser()


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/", response_model=dict)
async def upload_job_description(jd_data: JobDescriptionCreate, session: AsyncSession = Depends(get_session)):
    repo = JobDescriptionRepository(session)
    intent = _jd_parser.parse(jd_data.title, jd_data.description)

    jd = await repo.create(
        title=jd_data.title,
        raw_text=jd_data.description,
        structured_json=intent.to_dict(),
        required_skills=intent.required_skills,
        optional_skills=intent.optional_skills,
        experience_min=intent.experience_min,
        experience_max=intent.experience_max,
        behavioral_traits=intent.behavioral_traits,
    )

    return {
        "message": "Job description uploaded and parsed successfully",
        "job_description_id": jd.id,
        "title": jd.title,
        "required_skills": intent.required_skills[:10],
        "experience_range": [intent.experience_min, intent.experience_max],
    }


@router.get("/", response_model=List[dict])
async def list_job_descriptions(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session)):
    repo = JobDescriptionRepository(session)
    return [
        {
            "id": jd.id,
            "title": jd.title,
            "created_at": jd.created_at.isoformat() if jd.created_at else None,
        }
        for jd in await repo.get_all(skip=skip, limit=limit)
    ]


@router.get("/{jd_id}", response_model=dict)
async def get_job_description(jd_id: int, session: AsyncSession = Depends(get_session)):
    repo = JobDescriptionRepository(session)
    jd = await repo.get_by_id(jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return {
        "id": jd.id,
        "title": jd.title,
        "raw_text": jd.raw_text,
        "required_skills": jd.required_skills,
        "optional_skills": jd.optional_skills,
        "experience_min": jd.experience_min,
        "experience_max": jd.experience_max,
        "behavioral_traits": jd.behavioral_traits,
        "structured_json": jd.structured_json,
        "created_at": jd.created_at.isoformat() if jd.created_at else None,
    }


@router.delete("/{jd_id}", response_model=dict)
async def delete_job_description(jd_id: int, session: AsyncSession = Depends(get_session)):
    repo = JobDescriptionRepository(session)
    if not await repo.delete(jd_id):
        raise HTTPException(status_code=404, detail="Job description not found")
    return {"message": "Job description deleted", "job_description_id": jd_id}
