"""Predictions API router — retrieve hiring success predictions for candidates."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.repositories.prediction_repository import PredictionRepository
from app.schemas.prediction import PredictionResponse

router = APIRouter()


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/{candidate_id}", response_model=dict)
async def get_prediction(
    candidate_id: int,
    job_description_id: Optional[int] = Query(None, description="Filter by job description ID"),
    session: AsyncSession = Depends(get_session),
):
    """Get hiring success predictions for a candidate.

    If job_description_id is provided, returns prediction for that specific job.
    Otherwise returns the latest prediction for the candidate.
    """
    repo = PredictionRepository(session)
    predictions = await repo.get_for_candidate(
        candidate_id=candidate_id,
        job_description_id=job_description_id,
    )

    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for candidate {candidate_id}",
        )

    # Return most recent prediction
    p = predictions[0]
    return {
        "id": p.id,
        "candidate_id": p.candidate_id,
        "job_description_id": p.job_description_id,
        "success_probability": p.success_probability,
        "month_1_performance": p.month_1_performance,
        "month_3_performance": p.month_3_performance,
        "month_6_performance": p.month_6_performance,
        "reasoning": p.reasoning,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.get("/job/{job_description_id}", response_model=List[dict])
async def get_job_predictions(
    job_description_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """Get all predictions for a job description, ordered by probability descending."""
    repo = PredictionRepository(session)
    predictions = await repo.get_for_job(
        job_description_id=job_description_id,
        skip=skip,
        limit=limit,
    )

    return [
        {
            "id": p.id,
            "candidate_id": p.candidate_id,
            "job_description_id": p.job_description_id,
            "success_probability": p.success_probability,
            "month_1_performance": p.month_1_performance,
            "month_3_performance": p.month_3_performance,
            "month_6_performance": p.month_6_performance,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in predictions
    ]