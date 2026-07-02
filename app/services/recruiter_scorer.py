"""Unified recruiter-style candidate scoring engine.

Ranks candidates by role fit and career narrative — not keyword density.
Used by submission scripts, API analysis, and evaluation tools.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.services.candidate_utils import (
    build_career_narrative,
    candidate_display_id,
    normalize_candidate,
    title_text,
)
from app.services.feature_engineering import FeatureEngineering
from app.services.jd_intent import JobIntent, JobIntentParser

try:
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # pragma: no cover
    cosine_similarity = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None


ROLE_TIER_1 = [
    "search engineer", "recommendation systems", "recsys", "recsys engineer",
    "recommendation engineer", "ml engineer", "machine learning engineer",
    "nlp engineer", "applied scientist", "ai engineer", "applied ml engineer",
    "senior ml", "staff ml", "staff machine learning", "senior machine learning",
    "senior nlp", "senior ai", "lead ai", "lead ml", "information retrieval",
    "learning to rank", "ranking engineer",
]

ROLE_TIER_2 = [
    "data scientist", "senior data scientist", "software engineer (ml)",
    "software engineer ml", "backend engineer", "senior software engineer (ml)",
    "ml specialist", "ai specialist", "machine learning specialist",
]

ROLE_TIER_3 = [
    "data engineer", "analytics engineer", "ml engineer junior", "junior ml",
    "research engineer", "ai research engineer",
]

ROLE_TIER_LOW = [
    "frontend engineer", "front-end", "frontend developer", "mobile developer",
    "android developer", "ios developer", "qa engineer", "quality assurance",
    "java developer", ".net developer", "dotnet", "full stack developer",
    "fullstack", "devops engineer", "cloud engineer", "software engineer",
    "web developer", "ui developer", "ux engineer",
]

ROLE_REJECT = [
    "hr manager", "human resources", "accountant", "accounting", "marketing manager",
    "marketing ", "sales executive", "sales manager", "customer support", "support lead",
    "content writer", "copywriter", "graphic designer", "mechanical engineer",
    "civil engineer", "operations manager", "project manager", "business analyst",
    "financial analyst", "legal counsel", "recruiter", "talent acquisition",
]

CONSULTING_COMPANIES = [
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "tata consultancy", "mindtree", "ltimindtree", "hcl", "tech mahindra",
]

WRONG_DOMAIN_TERMS = [
    "computer vision", "speech recognition", "robotics", "autonomous driving",
    "object detection", "image classification", "opencv", "asr", "tts",
]

NLP_IR_TERMS = [
    "nlp", "natural language", "retrieval", "search", "ranking", "recommendation",
    "embedding", "semantic search", "information retrieval", "llm", "rag",
]

RETRIEVAL_RANKING_TERMS = [
    "information retrieval", "retrieval", "hybrid search", "hybrid retrieval",
    "semantic search", "vector search", "search relevance", "ranking",
    "learning to rank", "re-ranking", "reranking", "recommendation",
    "recommender", "candidate matching", "bm25",
]

EVALUATION_TERMS = [
    "ndcg", "mrr", "map@", "mean average precision", "precision@", "recall@",
    "offline evaluation", "online evaluation", "evaluation framework",
    "a/b test", "ab test", "interleaving", "offline-to-online",
    "recruiter feedback", "relevance judgment",
]

PRODUCTION_TERMS = [
    "production", "deployed", "shipped", "serving", "rollout", "launched",
    "latency", "throughput", "qps", "queries per", "users", "on-call",
    "monitoring", "regression", "index refresh", "drift",
]

HANDS_ON_TERMS = [
    "implemented", "built", "coded", "developed", "trained", "debugged",
    "optimized", "wrote", "python", "pytorch", "scikit-learn", "xgboost",
]

EXTERNAL_VALIDATION_TERMS = [
    "open source", "open-source", "github", "paper", "publication",
    "conference", "speaker", "talk", "maintainer", "contributor",
]

REFERENCE_DATE = date(2026, 6, 1)

COMPANY_FOUNDED_YEARS = {
    "anthropic": 2021,
    "cohere": 2019,
    "cred": 2018,
    "haptik": 2013,
    "hugging face": 2016,
    "krutrim": 2023,
    "niramai": 2016,
    "openai": 2015,
    "sarvam ai": 2023,
    "stability ai": 2019,
    "verloop.io": 2015,
    "yellow.ai": 2016,
}

KNOWN_BOILERPLATE = [
    "customer support team lead at a saas product",
    "senior accounting role at a mid-sized company",
    "mechanical engineering design role at a hardware-product company",
    "operations management role at a logistics company",
    "android mobile development using java and (more recently) kotlin",
    "enterprise sales of cloud software solutions",
    "marketing leadership role at a b2b saas company",
    "brand design and creative direction at a consumer-products company",
]

PROFICIENCY_WEIGHT = {
    "beginner": 0.25,
    "intermediate": 0.5,
    "advanced": 0.75,
    "expert": 1.0,
}


@dataclass
class ScoreBreakdown:
    candidate_id: str
    final_score: float
    role_fit: float
    career_coherence: float
    production_narrative: float
    retrieval_depth: float
    evaluation_depth: float
    hands_on_score: float
    skill_trust: float
    semantic_similarity: float
    behavioral: float
    technical_features: float
    experience_fit: float
    location_fit: float
    anti_pattern_multiplier: float
    availability_multiplier: float
    honeypot_penalty: float
    is_honeypot: bool
    is_reject_role: bool
    strengths: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    production_evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "final_score": self.final_score,
            "role_fit": self.role_fit,
            "career_coherence": self.career_coherence,
            "production_narrative": self.production_narrative,
            "retrieval_depth": self.retrieval_depth,
            "evaluation_depth": self.evaluation_depth,
            "hands_on_score": self.hands_on_score,
            "skill_trust": self.skill_trust,
            "semantic_similarity": self.semantic_similarity,
            "behavioral": self.behavioral,
            "technical_features": self.technical_features,
            "experience_fit": self.experience_fit,
            "location_fit": self.location_fit,
            "anti_pattern_multiplier": self.anti_pattern_multiplier,
            "availability_multiplier": self.availability_multiplier,
            "honeypot_penalty": self.honeypot_penalty,
            "is_honeypot": self.is_honeypot,
            "is_reject_role": self.is_reject_role,
            "strengths": self.strengths,
            "concerns": self.concerns,
            "production_evidence": self.production_evidence,
        }


class RecruiterScorer:
    """Score and rank candidates the way a strong recruiter would."""

    def __init__(
        self,
        job_intent: JobIntent,
        use_embeddings: bool = True,
        embedding_model: str = "BAAI/bge-small-en-v1.5",
        cache_dir: Optional[str] = "./cache",
    ):
        self.job_intent = job_intent
        self.use_embeddings = use_embeddings and SentenceTransformer is not None
        self.embedding_model_name = embedding_model
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.feature_engine = FeatureEngineering()
        self._embedder: Optional[Any] = None
        self._jd_embedding: Optional[np.ndarray] = None

        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_jd_text(cls, jd_text: str, title: str = "Senior AI Engineer", **kwargs) -> "RecruiterScorer":
        intent = JobIntentParser.from_text(jd_text, title)
        return cls(intent, **kwargs)

    @classmethod
    def default(cls, **kwargs) -> "RecruiterScorer":
        return cls(JobIntentParser.default_redrob(), **kwargs)

    @property
    def embedder(self):
        if self._embedder is None and self.use_embeddings:
            self._embedder = SentenceTransformer(self.embedding_model_name)
        return self._embedder

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        top_k: int = 100,
        coarse_pool: int = 5000,
        progress_every: int = 5000,
    ) -> Tuple[List[Dict[str, Any]], List[ScoreBreakdown]]:
        normalized = [normalize_candidate(c) for c in candidates]
        narratives = [build_career_narrative(c) for c in normalized]

        semantic_scores = self._compute_semantic_scores(narratives)

        coarse_scored: List[Tuple[int, float]] = []
        for idx, candidate in enumerate(normalized):
            quick = self._coarse_score(candidate, semantic_scores[idx])
            coarse_scored.append((idx, quick))
            if progress_every and (idx + 1) % progress_every == 0:
                print(f"  Coarse-scored {idx + 1}/{len(normalized)} candidates")

        coarse_scored.sort(key=lambda x: x[1], reverse=True)
        if len(normalized) <= coarse_pool:
            pool_indices = list(range(len(normalized)))
        else:
            pool_size = min(coarse_pool, len(coarse_scored))
            pool_indices = [idx for idx, _ in coarse_scored[:pool_size]]

        print(f"Deep-scoring top {len(pool_indices)} candidates...")
        breakdowns: List[ScoreBreakdown] = []
        for n, idx in enumerate(pool_indices, 1):
            features = self.feature_engine.extract_features(normalized[idx])
            breakdown = self.score_candidate(
                normalized[idx],
                semantic_score=semantic_scores[idx],
                features=features,
            )
            breakdowns.append(breakdown)
            if progress_every and n % max(1, progress_every // 5) == 0:
                print(f"  Deep-scored {n}/{len(pool_indices)} candidates")

        breakdowns.sort(
            key=lambda breakdown: (-round(breakdown.final_score, 6), breakdown.candidate_id)
        )
        eligible = [b for b in breakdowns if not b.is_reject_role and not b.is_honeypot]
        selected = eligible[:top_k]

        id_to_candidate = {candidate_display_id(c): c for c in normalized}
        results = []
        for rank, breakdown in enumerate(selected, 1):
            candidate = id_to_candidate[breakdown.candidate_id]
            results.append({
                "candidate_id": breakdown.candidate_id,
                "rank": rank,
                "score": round(breakdown.final_score, 6),
                "reasoning": self.build_reasoning(candidate, breakdown, rank),
                "breakdown": breakdown.to_dict(),
            })

        return results, breakdowns

    def score_candidate(
        self,
        candidate: Dict[str, Any],
        semantic_score: float = 0.0,
        features: Optional[Dict[str, float]] = None,
    ) -> ScoreBreakdown:
        candidate = normalize_candidate(candidate)
        cid = candidate_display_id(candidate)
        profile = candidate.get("profile", {}) or {}
        redrob = candidate.get("redrob_signals", {}) or {}
        career = candidate.get("career_history", []) or []

        features = features or self.feature_engine.extract_features(candidate)

        role_fit, is_reject = self._role_fit(candidate)
        coherence = self._career_coherence(candidate)
        production, evidence = self._production_narrative(candidate)
        retrieval_depth, evaluation_depth, hands_on_score = self._technical_depth(candidate)
        skill_trust = self._skill_trust(candidate)
        behavioral = float(features.get("behavioral_signals", 0.0))
        technical = (
            0.50 * retrieval_depth
            + 0.30 * evaluation_depth
            + 0.15 * hands_on_score
            + 0.05 * float(features.get("mlops_experience", 0.0))
        )
        experience_fit = self._experience_fit(profile.get("years_of_experience", 0))
        location_fit = self._location_fit(profile, redrob)
        anti_pattern = self._anti_pattern_multiplier(candidate, career, profile)
        availability = self._availability_multiplier(redrob)
        honeypot, honeypot_penalty = self._honeypot_assessment(candidate, role_fit, coherence)

        narrative_component = max(production, semantic_score * 0.65)

        base = (
            0.22 * role_fit
            + 0.20 * narrative_component
            + 0.18 * retrieval_depth
            + 0.12 * evaluation_depth
            + 0.08 * skill_trust
            + 0.07 * coherence
            + 0.05 * behavioral
            + 0.04 * experience_fit
            + 0.04 * hands_on_score
        )

        final = base * anti_pattern * availability * location_fit * honeypot_penalty
        if is_reject:
            final = min(final * 0.05, 0.02)

        strengths, concerns = self._summarize_signals(
            candidate, role_fit, production, skill_trust, coherence, evidence, features, redrob
        )

        return ScoreBreakdown(
            candidate_id=cid,
            final_score=float(max(0.0, min(1.0, final))),
            role_fit=role_fit,
            career_coherence=coherence,
            production_narrative=production,
            retrieval_depth=retrieval_depth,
            evaluation_depth=evaluation_depth,
            hands_on_score=hands_on_score,
            skill_trust=skill_trust,
            semantic_similarity=semantic_score,
            behavioral=behavioral,
            technical_features=technical,
            experience_fit=experience_fit,
            location_fit=location_fit,
            anti_pattern_multiplier=anti_pattern,
            availability_multiplier=availability,
            honeypot_penalty=honeypot_penalty,
            is_honeypot=honeypot,
            is_reject_role=is_reject,
            strengths=strengths,
            concerns=concerns,
            production_evidence=evidence,
        )

    def _build_reasoning_legacy(self, candidate: Dict[str, Any], breakdown: ScoreBreakdown, rank: int) -> str:
        profile = candidate.get("profile", {}) or {}
        redrob = candidate.get("redrob_signals", {}) or {}
        title = profile.get("current_title", "Candidate")
        company = profile.get("current_company", "")
        years = profile.get("years_of_experience", 0)
        location = profile.get("location", "")

        parts: List[str] = []

        if breakdown.role_fit >= 0.7:
            lead = title if not company else f"{title} at {company}"
            parts.append(f"{lead} — strong role fit for retrieval/ranking engineering")
        elif breakdown.is_reject_role:
            parts.append(f"{title} — role mismatch for Senior AI Engineer (non-ML career track)")
        else:
            parts.append(f"{title} with {years:.1f} yrs experience")

        if breakdown.production_evidence:
            parts.append(f"Career evidence: {breakdown.production_evidence[0]}")
        elif breakdown.production_narrative >= 0.5:
            parts.append("Career narrative shows production ML/search delivery")
        elif breakdown.production_narrative < 0.25:
            parts.append("Limited production retrieval/ranking evidence in career history")

        trusted = self._top_trusted_skills(candidate, limit=3)
        if trusted:
            parts.append(f"Trusted skills: {', '.join(trusted)}")

        signals = []
        response = redrob.get("recruiter_response_rate", 0)
        notice = redrob.get("notice_period_days", 90)
        if response and response > 0.5:
            signals.append(f"response rate {response:.0%}")
        if notice is not None and notice < 30:
            signals.append(f"notice {notice}d")
        if location and any(c in location.lower() for c in self.job_intent.preferred_locations):
            signals.append(f"based in {location}")
        if signals:
            parts.append("; ".join(signals))

        concern_pool = list(breakdown.concerns)
        if breakdown.is_honeypot:
            concern_pool.append("profile coherence flags (possible honeypot)")
        if rank > 30 and concern_pool:
            parts.append(f"Concerns: {', '.join(concern_pool[:3])}")

        return "; ".join(parts)

    def build_reasoning(self, candidate: Dict[str, Any], breakdown: ScoreBreakdown, rank: int) -> str:
        profile = candidate.get("profile", {}) or {}
        redrob = candidate.get("redrob_signals", {}) or {}
        title = str(profile.get("current_title", "Candidate"))
        company = str(profile.get("current_company", ""))
        years = float(profile.get("years_of_experience", 0) or 0)
        location = str(profile.get("location", ""))
        lead = title if not company else f"{title} at {company}"

        if breakdown.production_evidence:
            evidence = self._truncate_at_word(breakdown.production_evidence[0], 145)
            first_sentence = f"{lead} ({years:g} years) provides direct evidence: {evidence}."
        elif breakdown.retrieval_depth >= 0.5:
            first_sentence = (
                f"{lead} ({years:g} years) has career evidence across retrieval, ranking, "
                "or recommendation systems."
            )
        else:
            first_sentence = (
                f"{lead} ({years:g} years) has limited explicit production retrieval or ranking "
                "evidence in the recorded career history."
            )

        details: List[str] = []
        trusted = self._top_trusted_skills(candidate, limit=3)
        if trusted:
            details.append(f"evidence-backed skills include {', '.join(trusted)}")

        response = float(redrob.get("recruiter_response_rate", 0) or 0)
        notice = int(redrob.get("notice_period_days", 90) or 0)
        if response >= 0.5:
            details.append(f"recruiter response rate is {response:.0%}")
        if notice <= 30:
            details.append(f"notice period is {notice} days")
        if location and any(city in location.lower() for city in self.job_intent.primary_locations):
            details.append(f"location is {location}")

        concern_pool = list(breakdown.concerns)
        if breakdown.is_honeypot:
            concern_pool.append("profile coherence flags indicate possible synthetic data")
        if concern_pool:
            details.append(f"main concern: {concern_pool[0].lower()}")
        elif rank > 50:
            details.append("depth is weaker than candidates ranked above")

        if not details:
            return first_sentence
        second_sentence = details[0].capitalize()
        if len(details) > 1:
            second_sentence += "; " + "; ".join(details[1:])
        return f"{first_sentence} {second_sentence}."

    def _coarse_score(self, candidate: Dict[str, Any], semantic: float) -> float:
        role_fit, is_reject = self._role_fit(candidate)
        if is_reject:
            return 0.0
        production, _ = self._production_narrative(candidate)
        retrieval_depth, evaluation_depth, hands_on_score = self._technical_depth(candidate)
        honeypot, penalty = self._honeypot_assessment(
            candidate, role_fit, self._career_coherence(candidate)
        )
        if honeypot:
            return 0.0
        skill_trust = self._skill_trust(candidate)
        return (
            0.30 * role_fit
            + 0.25 * max(production, semantic * 0.65)
            + 0.22 * retrieval_depth
            + 0.10 * evaluation_depth
            + 0.08 * skill_trust
            + 0.05 * hands_on_score
        ) * penalty

    def _role_fit(self, candidate: Dict[str, Any]) -> Tuple[float, bool]:
        profile = candidate.get("profile", {}) or {}
        current_text = " ".join([
            str(profile.get("current_title", "")),
            str(profile.get("headline", "")),
        ]).lower()
        recent_titles = " ".join(
            str(entry.get("title", ""))
            for entry in (candidate.get("career_history", []) or [])[:2]
        ).lower()

        if not current_text.strip():
            return 0.2, False
        if any(term in current_text for term in ROLE_REJECT):
            return 0.02, True
        if any(term in current_text for term in ROLE_TIER_1):
            return 0.95, False
        if any(term in current_text for term in ROLE_TIER_2):
            return 0.76, False
        if any(term in current_text for term in ROLE_TIER_3):
            return 0.55, False
        if any(term in current_text for term in ROLE_TIER_LOW):
            if any(term in recent_titles for term in ROLE_TIER_1):
                return 0.48, False
            return 0.20, False
        if "backend engineer" in current_text or "backend developer" in current_text:
            return (0.58 if any(term in recent_titles for term in ROLE_TIER_1) else 0.38), False
        if "software engineer" in current_text:
            return (0.62 if any(term in recent_titles for term in ROLE_TIER_1) else 0.42), False
        if any(k in current_text for k in ["engineer", "scientist", "research", "developer"]):
            return 0.32, False
        return 0.15, False

    def _career_coherence(self, candidate: Dict[str, Any]) -> float:
        profile = candidate.get("profile", {}) or {}
        career = candidate.get("career_history", []) or []
        narrative = build_career_narrative(candidate)
        if not narrative:
            return 0.3

        score = 0.82
        current_title = str(profile.get("current_title", "")).lower()
        current_description = str(career[0].get("description", "")).lower() if career else ""
        reject_in_title = any(term in current_title for term in ROLE_REJECT)
        ml_in_narrative = sum(1 for t in NLP_IR_TERMS if t in narrative)
        ml_in_skills = sum(
            1 for s in candidate.get("skills", []) or []
            if any(t in str(s.get("name", "")).lower() for t in NLP_IR_TERMS)
        )
        if reject_in_title and (ml_in_narrative >= 2 or ml_in_skills >= 4):
            score -= 0.60

        for phrase in KNOWN_BOILERPLATE:
            if phrase in narrative:
                score -= 0.35
                break

        current_is_ml = any(term in current_title for term in ROLE_TIER_1 + ROLE_TIER_2)
        description_is_technical = any(
            term in current_description
            for term in RETRIEVAL_RANKING_TERMS + PRODUCTION_TERMS + HANDS_ON_TERMS
        )
        if current_is_ml and len(current_description) > 80 and not description_is_technical:
            score -= 0.25
        if reject_in_title and any(term in current_description for term in RETRIEVAL_RANKING_TERMS):
            score -= 0.20

        descriptions = [entry.get("description", "") for entry in career]
        if len(descriptions) >= 2:
            normalized = [re.sub(r"\s+", " ", d.lower().strip()) for d in descriptions if d]
            if normalized:
                most_common = Counter(normalized).most_common(1)[0]
                if most_common[1] >= 2 and len(most_common[0]) > 80:
                    score -= 0.30

        profile_months = float(profile.get("years_of_experience", 0) or 0) * 12
        career_months = sum(int(entry.get("duration_months", 0) or 0) for entry in career)
        if profile_months and career_months and abs(profile_months - career_months) > 42:
            score -= 0.18

        return float(max(0.0, min(1.0, score)))

    def _production_narrative(self, candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
        career = candidate.get("career_history", []) or []
        if not career:
            return 0.0, []

        production_score = 0.0
        evidence: List[str] = []
        for index, entry in enumerate(career):
            raw_description = re.sub(r"\s+", " ", str(entry.get("description", "")).strip())
            description = raw_description.lower()
            if not description or any(phrase in description for phrase in KNOWN_BOILERPLATE):
                continue
            recency_weight = 1.0 if index == 0 else 0.85 if index == 1 else 0.65
            production_hits = sum(term in description for term in PRODUCTION_TERMS)
            retrieval_hits = sum(term in description for term in RETRIEVAL_RANKING_TERMS)
            evaluation_hits = sum(term in description for term in EVALUATION_TERMS)
            quantified = bool(
                re.search(
                    r"\b\d+(?:\.\d+)?\s*(?:%|m\+?|million|k\+?|queries|users|ms|qps)\b",
                    description,
                )
            )
            entry_score = (
                min(0.32, production_hits * 0.08)
                + min(0.30, retrieval_hits * 0.07)
                + min(0.24, evaluation_hits * 0.08)
                + (0.10 if quantified else 0.0)
            ) * recency_weight
            production_score = max(production_score, entry_score)

            if entry_score >= 0.22:
                evidence.append(self._best_evidence_sentence(raw_description))

        return float(min(1.0, production_score)), evidence[:3]

    def _technical_depth(self, candidate: Dict[str, Any]) -> Tuple[float, float, float]:
        career = candidate.get("career_history", []) or []
        retrieval_score = 0.0
        evaluation_score = 0.0
        hands_on_score = 0.0

        for index, entry in enumerate(career):
            description = str(entry.get("description", "")).lower()
            title = str(entry.get("title", "")).lower()
            recency_weight = 1.0 if index == 0 else 0.8 if index == 1 else 0.55
            retrieval_hits = sum(term in description for term in RETRIEVAL_RANKING_TERMS)
            evaluation_hits = sum(term in description for term in EVALUATION_TERMS)
            hands_on_hits = sum(term in description for term in HANDS_ON_TERMS)

            retrieval_score = max(
                retrieval_score,
                min(1.0, retrieval_hits / 4.0) * recency_weight,
            )
            evaluation_score = max(
                evaluation_score,
                min(1.0, evaluation_hits / 2.0) * recency_weight,
            )
            hands_on_score = max(
                hands_on_score,
                min(1.0, hands_on_hits / 4.0) * recency_weight,
            )
            if any(term in title for term in ROLE_TIER_1) and retrieval_hits:
                retrieval_score = min(1.0, retrieval_score + 0.12 * recency_weight)

        return float(retrieval_score), float(evaluation_score), float(hands_on_score)

    def _best_evidence_sentence(self, text: str) -> str:
        sentences = [
            sentence.strip(" -")
            for sentence in re.split(r"(?<=[.!?])\s+", text)
            if sentence.strip()
        ]
        if not sentences:
            return self._truncate_at_word(text, 145)
        def evidence_score(sentence: str) -> int:
            lowered = sentence.lower()
            return (
                3 * sum(term in lowered for term in RETRIEVAL_RANKING_TERMS)
                + 2 * sum(term in lowered for term in EVALUATION_TERMS)
                + sum(term in lowered for term in PRODUCTION_TERMS)
            )

        best = max(sentences, key=evidence_score)
        return self._truncate_at_word(best, 145)

    def _truncate_at_word(self, text: str, limit: int) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip().rstrip(".")
        if len(cleaned) <= limit:
            return cleaned
        shortened = cleaned[:limit].rsplit(" ", 1)[0]
        return shortened.rstrip(" ,;:")

    def _skill_trust(self, candidate: Dict[str, Any]) -> float:
        skills = candidate.get("skills", []) or []
        if not skills:
            return 0.0

        core_terms = {
            term
            for term in self.job_intent.core_skill_terms + [skill.lower() for skill in self.job_intent.required_skills]
            if len(term) >= 4 or term in {"llm", "rag", "bge", "e5"}
        }
        trusted_hits = []
        noise_penalty = 0.0
        profile_months = float(
            (candidate.get("profile", {}) or {}).get("years_of_experience", 0) or 0
        ) * 12
        assessments = {
            str(name).lower(): float(score)
            for name, score in (candidate.get("redrob_signals", {}).get("skill_assessment_scores", {}) or {}).items()
        }

        for skill in skills:
            if not isinstance(skill, dict):
                continue
            name = str(skill.get("name", "")).lower()
            if not name:
                continue

            duration = int(skill.get("duration_months", 0) or 0)
            endorsements = int(skill.get("endorsements", 0) or 0)
            prof = PROFICIENCY_WEIGHT.get(str(skill.get("proficiency", "intermediate")).lower(), 0.5)
            duration_factor = min(1.0, duration / 24.0)
            endorse_factor = min(1.0, math.log1p(endorsements) / math.log1p(20))
            trust = (0.55 * duration_factor + 0.45 * endorse_factor) * prof

            if prof >= 0.75 and duration < 6 and endorsements < 3:
                noise_penalty += 0.05
            if profile_months and duration > profile_months + 12:
                trust *= 0.45
                noise_penalty += 0.03
            assessment = assessments.get(name)
            if assessment is not None:
                trust *= 0.65 + 0.35 * max(0.0, min(1.0, assessment / 100.0))

            if any(term in name for term in core_terms):
                trusted_hits.append(trust)
            elif any(term in name for term in WRONG_DOMAIN_TERMS):
                noise_penalty += 0.04

        if not trusted_hits:
            avg_trust = 0.15
        else:
            trusted_hits.sort(reverse=True)
            avg_trust = sum(trusted_hits[:6]) / len(trusted_hits[:6])

        # Transferability engine removed in cleanup; keep base trust score.

        return float(max(0.0, min(1.0, avg_trust - noise_penalty)))

    def _experience_fit(self, years: Any) -> float:
        try:
            y = float(years or 0)
        except (TypeError, ValueError):
            y = 0.0
        exp_min = self.job_intent.experience_min or 5
        exp_max = self.job_intent.experience_max or 9
        if exp_min <= y <= exp_max:
            return 1.0
        if exp_min - 1 <= y < exp_min or exp_max < y <= exp_max + 3:
            return 0.85
        if y < 3 or y > 16:
            return 0.45
        return 0.65

    def _location_fit(self, profile: Dict[str, Any], redrob: Dict[str, Any]) -> float:
        location = str(profile.get("location", "")).lower()
        country = str(profile.get("country", "")).lower()
        if country and country != "india":
            return 0.72 if redrob.get("willing_to_relocate") else 0.40
        if any(city in location for city in self.job_intent.primary_locations):
            return 1.05
        if any(city in location for city in self.job_intent.acceptable_locations):
            return 1.0
        return 0.94

    def _anti_pattern_multiplier(
        self,
        candidate: Dict[str, Any],
        career: List[Dict[str, Any]],
        profile: Dict[str, Any],
    ) -> float:
        multiplier = 1.0
        summary = str(profile.get("summary", "")).lower()
        companies = [str(e.get("company", "")).lower() for e in career]

        if "lately i've been curious about how ai tools" in summary or "experimented with chatgpt" in summary:
            multiplier *= 0.55

        non_consulting = [c for c in companies if c and not any(x in c for x in CONSULTING_COMPANIES)]
        if companies and not non_consulting:
            multiplier *= 0.55

        if len(career) >= 3:
            avg_tenure = np.mean([int(e.get("duration_months", 12) or 12) for e in career])
            if avg_tenure < 20:
                multiplier *= 0.72

        skill_names = [str(s.get("name", "")).lower() for s in candidate.get("skills", []) or []]
        framework_hits = sum(1 for s in skill_names if s in {"langchain", "llamaindex", "streamlit", "gradio"})
        if framework_hits >= 3 and not any(k in summary for k in ["production", "deployed", "shipped", "users"]):
            multiplier *= 0.72

        title_blob = title_text(candidate)
        wrong_domain = any(t in title_blob for t in WRONG_DOMAIN_TERMS)
        has_nlp = any(t in summary or t in " ".join(skill_names) for t in NLP_IR_TERMS)
        if wrong_domain and not has_nlp:
            multiplier *= 0.5

        if any(k in summary for k in ["research", "phd", "publication", "academic"]) and \
           not any(k in summary for k in ["production", "deployed", "shipped"]):
            multiplier *= 0.65

        current_description = str(career[0].get("description", "")).lower() if career else ""
        senior_title = any(
            term in str(profile.get("current_title", "")).lower()
            for term in ["senior", "staff", "principal", "lead", "architect"]
        )
        if senior_title and not any(term in current_description for term in HANDS_ON_TERMS):
            multiplier *= 0.86

        years = float(profile.get("years_of_experience", 0) or 0)
        redrob = candidate.get("redrob_signals", {}) or {}
        github = float(redrob.get("github_activity_score", -1) if redrob.get("github_activity_score") is not None else -1)
        narrative = build_career_narrative(candidate)
        if years >= 5 and github < 0 and not any(term in narrative for term in EXTERNAL_VALIDATION_TERMS):
            multiplier *= 0.92

        return float(multiplier)

    def _availability_multiplier(self, redrob: Dict[str, Any]) -> float:
        multiplier = 1.0
        if redrob.get("open_to_work_flag") is False:
            multiplier *= 0.72
        response = float(redrob.get("recruiter_response_rate", 0) or 0)
        if response < 0.2:
            multiplier *= 0.78
        elif response > 0.7:
            multiplier *= 1.05

        response_hours = float(redrob.get("avg_response_time_hours", 0) or 0)
        if response_hours > 168:
            multiplier *= 0.88
        elif 0 < response_hours <= 24:
            multiplier *= 1.03

        interview = float(redrob.get("interview_completion_rate", 0) or 0)
        if interview and interview < 0.5:
            multiplier *= 0.88

        notice = int(redrob.get("notice_period_days", 90) or 0)
        if notice > 90:
            multiplier *= 0.76
        elif notice > 60:
            multiplier *= 0.84
        elif notice > 30:
            multiplier *= 0.93
        elif notice <= 15:
            multiplier *= 1.03

        last_active = self._parse_date(redrob.get("last_active_date"))
        if last_active:
            inactive_days = (REFERENCE_DATE - last_active).days
            if inactive_days > 180:
                multiplier *= 0.58
            elif inactive_days > 90:
                multiplier *= 0.76
            elif inactive_days <= 30:
                multiplier *= 1.04

        github_value = redrob.get("github_activity_score", -1)
        github = float(github_value if github_value is not None else -1)
        if github > 50:
            multiplier *= 1.03
        return float(max(0.35, min(1.12, multiplier)))

    def _honeypot_assessment(
        self,
        candidate: Dict[str, Any],
        role_fit: float,
        coherence: float,
    ) -> Tuple[bool, float]:
        skills = candidate.get("skills", []) or []
        career = candidate.get("career_history", []) or []
        profile = candidate.get("profile", {}) or {}
        expert = [skill for skill in skills if str(skill.get("proficiency", "")).lower() == "expert"]
        profile_months = float(profile.get("years_of_experience", 0) or 0) * 12
        risk = 0.0

        shallow_experts = [
            skill for skill in expert
            if int(skill.get("duration_months", 0) or 0) < 6
            and int(skill.get("endorsements", 0) or 0) < 3
        ]
        if len(shallow_experts) >= 4:
            risk += 0.30
        if profile_months and sum(
            int(skill.get("duration_months", 0) or 0) > profile_months + 12
            for skill in skills
        ) >= 2:
            risk += 0.25
        if len([entry for entry in career if entry.get("is_current")]) > 1:
            risk += 0.45
        if role_fit < 0.15 and len(skills) >= 6:
            risk += 0.25
        if coherence < 0.25:
            risk += 0.30

        career_months = sum(int(entry.get("duration_months", 0) or 0) for entry in career)
        if profile_months and career_months and abs(profile_months - career_months) > 42:
            risk += 0.35
        summary = str(profile.get("summary", ""))
        summary_years_match = re.search(
            r"\b(\d+(?:\.\d+)?)\+?\s+(?:years|yrs)\b",
            summary,
            re.IGNORECASE,
        )
        if summary_years_match and profile_months:
            summary_years = float(summary_years_match.group(1))
            if abs(summary_years - profile_months / 12.0) > 2.5:
                risk += 0.35

        reject_title = any(term in title_text(candidate) for term in ROLE_REJECT)
        ai_skill_count = sum(
            1 for skill in skills
            if any(term in str(skill.get("name", "")).lower() for term in NLP_IR_TERMS)
        )
        if reject_title and ai_skill_count >= 5:
            risk += 0.55

        chronology_flags = 0
        founded_violation = False
        for entry in career:
            start = self._parse_date(entry.get("start_date"))
            end = self._parse_date(entry.get("end_date")) or (REFERENCE_DATE if entry.get("is_current") else None)
            duration = int(entry.get("duration_months", 0) or 0)
            if start and end:
                expected = max(0, (end.year - start.year) * 12 + end.month - start.month)
                if abs(expected - duration) > 5:
                    chronology_flags += 1
            company = str(entry.get("company", "")).strip().lower()
            founded = COMPANY_FOUNDED_YEARS.get(company)
            if founded and start and start.year < founded:
                founded_violation = True
        risk += min(0.36, chronology_flags * 0.18)
        if founded_violation:
            risk += 0.55

        assessments = {
            str(name).lower(): float(score)
            for name, score in (candidate.get("redrob_signals", {}).get("skill_assessment_scores", {}) or {}).items()
        }
        contradictions = 0
        for skill in expert:
            score = assessments.get(str(skill.get("name", "")).lower())
            if score is not None and score < 40:
                contradictions += 1
        if contradictions >= 3:
            risk += 0.22

        is_honeypot = risk >= 0.65
        if is_honeypot:
            return True, 0.05
        if risk >= 0.45:
            return False, 0.40
        if risk >= 0.25:
            return False, 0.75
        return False, 1.0

    def _parse_date(self, value: Any) -> Optional[date]:
        if not value:
            return None
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    def _summarize_signals(
        self,
        candidate: Dict[str, Any],
        role_fit: float,
        production: float,
        skill_trust: float,
        coherence: float,
        evidence: List[str],
        features: Dict[str, float],
        redrob: Dict[str, Any],
    ) -> Tuple[List[str], List[str]]:
        strengths: List[str] = []
        concerns: List[str] = []

        if role_fit >= 0.75:
            strengths.append("Title aligns with ML/search engineering track")
        if production >= 0.5:
            strengths.append("Career history cites production retrieval/ranking work")
        if skill_trust >= 0.55:
            strengths.append("Skills backed by duration and endorsements")
        if features.get("retrieval_experience", 0) > 0.5 or features.get("ranking_experience", 0) > 0.5:
            strengths.append("Strong retrieval/ranking feature profile")
        retrieval_depth, evaluation_depth, hands_on_score = self._technical_depth(candidate)
        if retrieval_depth >= 0.65:
            strengths.append("Career evidence shows retrieval or ranking depth")
        if evaluation_depth >= 0.6:
            strengths.append("Has hands-on ranking evaluation evidence")
        if hands_on_score >= 0.6:
            strengths.append("Recent career history contains hands-on implementation evidence")
        if redrob.get("recruiter_response_rate", 0) > 0.5:
            strengths.append("Engaged on platform")

        if coherence < 0.35:
            concerns.append("Title and career story appear misaligned")
        if production < 0.25 and not evidence:
            concerns.append("Weak production narrative for this JD")
        if skill_trust < 0.3:
            concerns.append("Skills look inflated vs tenure/endorsements")
        if redrob.get("open_to_work_flag") is False:
            concerns.append("Not actively open to work")
        notice = redrob.get("notice_period_days")
        if notice is not None and notice > 60:
            concerns.append(f"Long notice period ({notice}d)")
        profile = candidate.get("profile", {}) or {}
        years = float(profile.get("years_of_experience", 0) or 0)
        if years < 4:
            concerns.append(f"Experience below the preferred range ({years:g} years)")
        elif years > 12:
            concerns.append(f"Experience well above the preferred range ({years:g} years)")
        last_active = self._parse_date(redrob.get("last_active_date"))
        if last_active and (REFERENCE_DATE - last_active).days > 90:
            concerns.append("Low recent platform activity")

        return strengths, concerns

    def _top_trusted_skills(self, candidate: Dict[str, Any], limit: int = 3) -> List[str]:
        ranked = []
        core_terms = set(self.job_intent.core_skill_terms)
        for skill in candidate.get("skills", []) or []:
            if not isinstance(skill, dict):
                continue
            name = str(skill.get("name", ""))
            if not name:
                continue
            duration = int(skill.get("duration_months", 0) or 0)
            endorsements = int(skill.get("endorsements", 0) or 0)
            prof = PROFICIENCY_WEIGHT.get(str(skill.get("proficiency", "intermediate")).lower(), 0.5)
            trust = (min(1.0, duration / 24.0) * 0.6 + min(1.0, math.log1p(endorsements) / 3.0) * 0.4) * prof
            if any(t in name.lower() for t in core_terms):
                ranked.append((trust, name))
        ranked.sort(reverse=True)
        return [name for _, name in ranked[:limit]]

    def _compute_semantic_scores(self, narratives: List[str]) -> List[float]:
        if not self.use_embeddings or not narratives:
            return [0.0] * len(narratives)

        cache_path = self.cache_dir / "narrative_embeddings.npy" if self.cache_dir else None
        meta_path = self.cache_dir / "narrative_meta.json" if self.cache_dir else None

        embeddings = None
        fingerprint = hashlib.sha256()
        for narrative in narratives:
            fingerprint.update(narrative.encode("utf-8", errors="ignore"))
            fingerprint.update(b"\0")
        narrative_fingerprint = fingerprint.hexdigest()
        if cache_path and meta_path and cache_path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if (
                meta.get("count") == len(narratives)
                and meta.get("model") == self.embedding_model_name
                and meta.get("fingerprint") == narrative_fingerprint
            ):
                embeddings = np.load(cache_path)

        if embeddings is None:
            print(f"Computing narrative embeddings ({self.embedding_model_name})...")
            embeddings = self.embedder.encode(narratives, convert_to_numpy=True, show_progress_bar=True)
            if cache_path is not None and meta_path is not None:
                np.save(cache_path, embeddings)
                meta_path.write_text(
                    json.dumps({
                        "count": len(narratives),
                        "model": self.embedding_model_name,
                        "fingerprint": narrative_fingerprint,
                    }),
                    encoding="utf-8",
                )

        if self._jd_embedding is None:
            self._jd_embedding = self.embedder.encode(
                [self.job_intent.intent_document], convert_to_numpy=True, show_progress_bar=False
            )

        if cosine_similarity is None:
            return [0.0] * len(narratives)

        sims = cosine_similarity(self._jd_embedding, embeddings)[0]
        return [float(max(0.0, s)) for s in sims.tolist()]
