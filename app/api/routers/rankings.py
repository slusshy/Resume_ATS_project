"""Rankings API router — retrieve ranked candidates for a job description."""

from typing import List, Optional
import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.repositories.ranking_repository import RankingRepository
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.ranking import RankingResponse

router = APIRouter()


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/", response_model=List[dict])
async def get_rankings(
    job_description_id: int = Query(..., description="Job description ID to get rankings for"),
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """Get all rankings for a specific job description, ordered by overall score descending."""
    repo = RankingRepository(session)
    rankings = await repo.get_for_job(
        job_description_id=job_description_id,
        skip=skip,
        limit=limit,
    )

    results = []
    for rank_idx, r in enumerate(rankings, 1):
        results.append({
            "rank": rank_idx,
            "candidate_id": r.candidate_id,
            "job_description_id": r.job_description_id,
            "overall_score": r.overall_score,
            "technical_fit_score": r.technical_fit_score,
            "behavioral_fit_score": r.behavioral_fit_score,
            "learning_agility_score": r.learning_agility_score,
            "stability_score": r.stability_score,
            "growth_potential_score": r.growth_potential_score,
            "explanations": r.explanations,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return results


@router.get("/{candidate_id}", response_model=dict)
async def get_candidate_ranking(
    candidate_id: int,
    job_description_id: int = Query(..., description="Job description ID"),
    session: AsyncSession = Depends(get_session),
):
    """Get ranking for a specific candidate and job description pair."""
    repo = RankingRepository(session)
    ranking = await repo.get_for_candidate_and_job(
        candidate_id=candidate_id,
        job_description_id=job_description_id,
    )

    if not ranking:
        raise HTTPException(
            status_code=404,
            detail=f"Ranking not found for candidate {candidate_id} and job {job_description_id}",
        )

    return {
        "id": ranking.id,
        "candidate_id": ranking.candidate_id,
        "job_description_id": ranking.job_description_id,
        "overall_score": ranking.overall_score,
        "technical_fit_score": ranking.technical_fit_score,
        "behavioral_fit_score": ranking.behavioral_fit_score,
        "learning_agility_score": ranking.learning_agility_score,
        "stability_score": ranking.stability_score,
        "growth_potential_score": ranking.growth_potential_score,
        "explanations": ranking.explanations,
        "created_at": ranking.created_at.isoformat() if ranking.created_at else None,
    }


@router.get("/export/csv", response_class=StreamingResponse)
async def export_rankings_csv(
    job_description_id: int = Query(..., description="Job description ID to export rankings for"),
    session: AsyncSession = Depends(get_session),
):
    """Export rankings for a job description as downloadable CSV file."""
    repo = RankingRepository(session)
    rankings = await repo.get_for_job(
        job_description_id=job_description_id,
        skip=0,
        limit=1000,
    )

    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "rank", "candidate_id", "job_description_id", "overall_score",
        "technical_fit_score", "behavioral_fit_score", "learning_agility_score",
        "stability_score", "growth_potential_score", "reasoning"
    ])
    
    # Write data rows
    for rank_idx, r in enumerate(rankings, 1):
        explanations = r.explanations if isinstance(r.explanations, dict) else {}
        reasoning = explanations.get("summary", str(explanations)) if explanations else ""
        
        writer.writerow([
            rank_idx,
            r.candidate_id,
            r.job_description_id,
            round(r.overall_score, 6),
            round(r.technical_fit_score, 6),
            round(r.behavioral_fit_score, 6),
            round(r.learning_agility_score, 6),
            round(r.stability_score, 6),
            round(r.growth_potential_score, 6),
            reasoning[:500] if reasoning else ""  # Limit reasoning length
        ])
    
    # Reset buffer position
    output.seek(0)
    
    # Return as streaming response
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=rankings_job_{job_description_id}.csv"
        }
    )