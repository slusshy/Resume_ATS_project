"""Analysis orchestration service — uses unified RecruiterScorer."""

from __future__ import annotations

from typing import Any, Dict, List

from app.services.candidate_utils import candidate_db_id, candidate_display_id, normalize_candidate
from app.services.jd_intent import JobIntentParser
from app.services.recruiter_scorer import RecruiterScorer


class AnalysisService:
    """Run end-to-end candidate analysis with recruiter-style scoring."""

    def __init__(self, use_embeddings: bool = False, cache_dir: str = "./cache"):
        self.use_embeddings = use_embeddings
        self.cache_dir = cache_dir

    async def run_full_analysis(
        self,
        job_description: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        intent = JobIntentParser().parse(
            title=job_description.get("title", "Role"),
            description=job_description.get("description") or job_description.get("raw_text", ""),
        )

        normalized = [normalize_candidate(c) for c in candidates]
        scorer = RecruiterScorer(intent, use_embeddings=self.use_embeddings, cache_dir=self.cache_dir)

        top_k = min(100, len(normalized))
        ranked_rows, breakdowns = scorer.rank_candidates(
            normalized,
            top_k=top_k,
            coarse_pool=min(500, len(normalized)),  # Reduced from 5000 to 500 for speed
            progress_every=0,
        )

        breakdown_map = {b.candidate_id: b for b in breakdowns}
        id_to_candidate = {candidate_display_id(c): c for c in normalized}

        detailed_results = []
        for row in ranked_rows:
            cid = row["candidate_id"]
            candidate = id_to_candidate.get(cid, {})
            breakdown = breakdown_map.get(cid)
            profile = candidate.get("profile", {}) or {}

            detailed_results.append({
                "rank": row["rank"],
                "candidate_id": candidate_db_id(candidate) or cid,
                "external_candidate_id": cid,
                "name": profile.get("anonymized_name") or candidate.get("name", "Unknown"),
                "overall_score": row["score"],
                "component_scores": row.get("breakdown", {}),
                "reasoning": {
                    "summary": row["reasoning"],
                    "strengths": breakdown.strengths if breakdown else [],
                    "weaknesses": breakdown.concerns if breakdown else [],
                    "why_shortlisted": row["reasoning"],
                    "risk_level": "High" if breakdown and breakdown.is_honeypot else (
                        "Medium" if breakdown and breakdown.concerns else "Low"
                    ),
                },
                "prediction": self._simple_prediction(row["score"], breakdown),
            })

        honeypots_in_top = sum(
            1 for row in ranked_rows
            if row.get("breakdown", {}).get("is_honeypot")
        )

        return {
            "job_description_id": job_description.get("id"),
            "job_title": job_description.get("title", ""),
            "total_candidates_analyzed": len(normalized),
            "total_ranked": len(detailed_results),
            "honeypots_in_top100": honeypots_in_top,
            "rankings": detailed_results,
        }

    def _simple_prediction(self, score: float, breakdown) -> Dict[str, Any]:
        success = min(0.95, max(0.05, score))
        return {
            "success_probability": round(success, 3),
            "month_1_performance": round(success * 0.85, 3),
            "month_3_performance": round(success * 0.92, 3),
            "month_6_performance": round(success, 3),
            "reasoning": (
                "Strong recruiter-style fit across role, narrative, and availability signals"
                if score >= 0.65
                else "Moderate fit — review concerns before advancing"
            ),
            "role_fit": breakdown.role_fit if breakdown else 0.0,
            "production_narrative": breakdown.production_narrative if breakdown else 0.0,
        }
