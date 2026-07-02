"""Normalize candidate records from JSONL, API uploads, or database models."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


def normalize_candidate(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Return a Redrob-schema candidate dict regardless of source shape."""
    if raw.get("candidate_id") and raw.get("profile"):
        return raw

    profile_json = raw.get("profile_json") or {}
    if isinstance(profile_json, str):
        try:
            profile_json = json.loads(profile_json)
        except json.JSONDecodeError:
            profile_json = {}

    if profile_json.get("candidate_id"):
        return profile_json

    raw_profile = raw.get("raw_profile") or raw.get("profile_text") or ""
    if isinstance(raw_profile, str) and raw_profile.strip().startswith("{"):
        try:
            parsed = json.loads(raw_profile)
            if parsed.get("candidate_id"):
                return parsed
        except json.JSONDecodeError:
            pass

    profile = raw.get("profile") or profile_json.get("profile") or {}
    career = raw.get("career_history") or profile_json.get("career_history") or []
    skills = raw.get("skills") or profile_json.get("skills") or []
    redrob = raw.get("redrob_signals") or profile_json.get("redrob_signals") or {}

    candidate_id = (
        raw.get("candidate_id")
        or profile_json.get("candidate_id")
        or raw.get("external_id")
        or f"LOCAL_{raw.get('id', 'unknown')}"
    )

    return {
        "candidate_id": str(candidate_id),
        "profile": profile if profile else {
            "anonymized_name": raw.get("name", "Unknown"),
            "headline": raw_profile[:200] if isinstance(raw_profile, str) else "",
            "summary": raw_profile if isinstance(raw_profile, str) else "",
            "location": "",
            "country": "",
            "years_of_experience": raw.get("experience_years") or 0,
            "current_title": raw.get("name", "Unknown"),
            "current_company": "",
            "current_company_size": "",
            "current_industry": "",
        },
        "career_history": career,
        "education": raw.get("education") or profile_json.get("education") or [],
        "skills": skills,
        "certifications": raw.get("certifications") or profile_json.get("certifications") or [],
        "redrob_signals": redrob,
        "_source_id": raw.get("id"),
    }


def candidate_display_id(candidate: Dict[str, Any]) -> str:
    return str(candidate.get("candidate_id") or candidate.get("_source_id") or "unknown")


def candidate_db_id(candidate: Dict[str, Any]) -> Optional[int]:
    value = candidate.get("_source_id") or candidate.get("id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def build_career_narrative(candidate: Dict[str, Any]) -> str:
    """Career story without skill tags — what a recruiter reads first."""
    profile = candidate.get("profile", {}) or {}
    parts = [
        profile.get("headline", ""),
        profile.get("summary", ""),
        profile.get("current_title", ""),
        profile.get("current_company", ""),
        profile.get("current_industry", ""),
    ]
    for entry in candidate.get("career_history", []) or []:
        parts.extend([
            entry.get("title", ""),
            entry.get("company", ""),
            entry.get("industry", ""),
            entry.get("description", ""),
        ])
    return _clean_text(" ".join(parts))


def build_skill_context(candidate: Dict[str, Any]) -> str:
    """Skill names with proficiency for trust scoring."""
    chunks = []
    for skill in candidate.get("skills", []) or []:
        if not isinstance(skill, dict):
            chunks.append(str(skill))
            continue
        chunks.append(
            f"{skill.get('name', '')} ({skill.get('proficiency', 'unknown')}, "
            f"{skill.get('duration_months', 0)}mo, {skill.get('endorsements', 0)} endorsements)"
        )
    return _clean_text(" ".join(chunks))


def title_text(candidate: Dict[str, Any]) -> str:
    profile = candidate.get("profile", {}) or {}
    titles = [profile.get("headline", ""), profile.get("current_title", "")]
    for entry in (candidate.get("career_history", []) or [])[:2]:
        titles.append(entry.get("title", ""))
    return _clean_text(" ".join(titles))


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()
