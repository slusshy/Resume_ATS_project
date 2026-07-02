"""Candidate upload API router."""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.candidate import CandidateCreate
from app.services.candidate_utils import normalize_candidate

router = APIRouter()


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


def _parse_upload_payload(item: CandidateCreate) -> dict:
    """Parse Redrob JSON profile or plain text into structured storage."""
    raw = item.profile_text.strip()
    profile_json = {}

    if raw.startswith("{"):
        try:
            profile_json = json.loads(raw)
        except json.JSONDecodeError:
            profile_json = {}

    normalized = normalize_candidate({
        "name": item.name,
        "profile_text": raw,
        "profile_json": profile_json,
    })

    profile = normalized.get("profile", {})
    skills = [s.get("name", "") for s in normalized.get("skills", []) if isinstance(s, dict)]

    # Try to use Gemini to extract additional information from raw profile
    extracted_info = {}
    if settings.GEMINI_API_KEY:
        try:
            from app.services.gemini_service import get_gemini_service

            gemini_service = get_gemini_service()
            extracted_info = gemini_service.extract_candidate_info(raw)
        except Exception as exc:
            print(f"Gemini extraction failed, using fallback: {exc}")

    # Don't use "Unknown" name from Gemini, use original name
    gemini_name = extracted_info.get("name")
    if gemini_name and gemini_name != "Unknown":
        name = gemini_name
    else:
        name = profile.get("anonymized_name") or item.name

    return {
        "name": name,
        "raw_profile": raw,
        "profile_json": normalized,
        "skills": extracted_info.get("skills", skills),
        "experience_years": extracted_info.get("experience_years") or int(float(profile.get("years_of_experience") or 0)),
        "languages": extracted_info.get("languages", []),
        "education": extracted_info.get("education"),
        "certifications": extracted_info.get("certifications", [c.get("name", "") for c in normalized.get("certifications", []) if isinstance(c, dict)]),
        "projects": extracted_info.get("projects", []),
        "summary": extracted_info.get("summary"),
    }


@router.post("/", response_model=dict)
async def upload_candidates(
    candidates_data: List[CandidateCreate],
    session: AsyncSession = Depends(get_session),
):
    repo = CandidateRepository(session)
    created = []

    for item in candidates_data:
        payload = _parse_upload_payload(item)
        candidate = await repo.create(**payload)
        created.append({"id": candidate.id, "name": candidate.name})

    return {
        "message": f"{len(created)} candidate(s) uploaded successfully",
        "candidates": created,
    }


@router.get("/", response_model=List[dict])
async def list_candidates(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session)):
    repo = CandidateRepository(session)
    candidates = await repo.get_all(skip=skip, limit=limit)
    return [
        {
            "id": c.id,
            "name": c.name,
            "experience_years": c.experience_years,
            "skills": c.skills,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in candidates
    ]


@router.get("/count", response_model=dict)
async def count_candidates(session: AsyncSession = Depends(get_session)):
    repo = CandidateRepository(session)
    return {"total": await repo.count()}


@router.get("/{candidate_id}", response_model=dict)
async def get_candidate(candidate_id: int, session: AsyncSession = Depends(get_session)):
    repo = CandidateRepository(session)
    candidate = await repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # If Gemini-extracted fields are missing, extract them now
    if settings.GEMINI_API_KEY and not candidate.summary and candidate.raw_profile:
        try:
            from app.services.gemini_service import get_gemini_service

            gemini_service = get_gemini_service()
            extracted = gemini_service.extract_candidate_info(candidate.raw_profile)
            # Don't override name with "Unknown"
            if extracted.get("name") == "Unknown":
                extracted.pop("name", None)
            # Update the candidate with extracted info
            await repo.update(candidate_id, **extracted)
            # Refresh the candidate object
            await session.commit()
            await session.refresh(candidate)
        except Exception as exc:
            print(f"Failed to extract candidate info on demand: {exc}")
    
    return {
        "id": candidate.id,
        "name": candidate.name,
        "raw_profile": candidate.raw_profile,
        "profile_json": candidate.profile_json,
        "skills": candidate.skills,
        "experience_years": candidate.experience_years,
        "languages": candidate.languages,
        "education": candidate.education,
        "certifications": candidate.certifications,
        "projects": candidate.projects,
        "summary": candidate.summary,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
    }


@router.delete("/{candidate_id}", response_model=dict)
async def delete_candidate(candidate_id: int, session: AsyncSession = Depends(get_session)):
    repo = CandidateRepository(session)
    if not await repo.delete(candidate_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate deleted", "candidate_id": candidate_id}
