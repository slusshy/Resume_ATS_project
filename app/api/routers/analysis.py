"""Analysis orchestration API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.ranking_repository import RankingRepository
from app.schemas.analysis import AnalysisRequest
from app.services.analysis_service import AnalysisService

router = APIRouter()


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/", response_model=dict)
async def analyze(request: AnalysisRequest, session: AsyncSession = Depends(get_session)):
    jd_repo = JobDescriptionRepository(session)
    candidate_repo = CandidateRepository(session)

    jd = await jd_repo.get_by_id(request.job_description_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    # If candidate_ids not provided, fetch candidates and rank them
    if request.candidate_ids:
        candidates = await candidate_repo.get_by_ids(request.candidate_ids)
    else:
        # Get recent candidates (limit to 5000 for performance)
        # System will rank and return top 100 from this pool
        candidates = await candidate_repo.get_all(
            skip=0,
            limit=settings.ANALYSIS_CANDIDATE_LIMIT,
        )
    
    if not candidates:
        raise HTTPException(status_code=404, detail="No candidates found")

    jd_dict = {
        "id": jd.id,
        "title": jd.title,
        "description": jd.raw_text,
        "required_skills": jd.required_skills or [],
        "optional_skills": jd.optional_skills or [],
        "experience_min": jd.experience_min,
        "experience_max": jd.experience_max,
        "behavioral_traits": jd.behavioral_traits or [],
    }

    candidates_dicts = []
    for candidate in candidates:
        profile_json = candidate.profile_json or {}
        candidates_dicts.append({
            "id": candidate.id,
            "name": candidate.name,
            "raw_profile": candidate.raw_profile,
            **profile_json,
        })

    analysis_service = AnalysisService(use_embeddings=settings.ENABLE_EMBEDDINGS)
    results = await analysis_service.run_full_analysis(jd_dict, candidates_dicts)

    # Gemini enhancement disabled - requires API key configuration
    # To enable: set GEMINI_API_KEY in .env and uncomment below
    """
    try:
        gemini_service = get_gemini_service()
        for item in results.get("rankings", []):
            candidate_id = item["candidate_id"]
            candidate = next((c for c in candidates if c.id == candidate_id), None)
            if candidate:
                candidate_profile = {
                    "name": candidate.name,
                    "experience_years": candidate.experience_years,
                    "skills": candidate.skills or [],
                    "languages": candidate.languages or [],
                    "education": candidate.education,
                    "certifications": candidate.certifications or [],
                    "projects": candidate.projects or [],
                    "summary": candidate.summary,
                }
                fit_analysis = gemini_service.analyze_candidate_fit(candidate_profile, jd.raw_text)
                item["gemini_analysis"] = fit_analysis
    except Exception as e:
        print(f"Gemini analysis enhancement failed: {e}")
    """

    ranking_repo = RankingRepository(session)
    prediction_repo = PredictionRepository(session)
    await ranking_repo.delete_for_job(jd.id)
    await prediction_repo.delete_for_job(jd.id)

    ranking_records = []
    for item in results.get("rankings", []):
        scores = item.get("component_scores", {})
        reasoning = item.get("reasoning", {})
        gemini_data = item.get("gemini_analysis", {})
        
        ranking_records.append({
            "candidate_id": item["candidate_id"],
            "job_description_id": jd.id,
            "technical_fit_score": scores.get("technical_features", scores.get("production_narrative", 0.0)),
            "behavioral_fit_score": scores.get("behavioral", 0.0),
            "learning_agility_score": scores.get("skill_trust", 0.0),
            "stability_score": scores.get("career_coherence", 0.0),
            "growth_potential_score": scores.get("role_fit", 0.0),
            "overall_score": item["overall_score"],
            "explanations": reasoning,
            "gemini_fit_score": gemini_data.get("fit_score"),
            "gemini_reasoning": gemini_data.get("reasoning"),
        })

    if ranking_records:
        await ranking_repo.bulk_create(ranking_records)

    return {
        "analysis_id": f"analysis_{jd.id}_{len(candidates_dicts)}",
        "job_title": results["job_title"],
        "total_candidates_analyzed": results["total_candidates_analyzed"],
        "total_ranked": results["total_ranked"],
        "honeypots_in_top100": results.get("honeypots_in_top100", 0),
        "rankings": results["rankings"],
    }
