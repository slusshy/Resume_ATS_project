"""Feature engineering module for RecruiterMind AI."""

import re
from typing import Any, Dict, List, Optional


class FeatureEngineering:
    """Extract numerical candidate features from the Redrob candidate schema."""

    TECHNICAL_BUCKETS = {
        "ai_ml": [
            "machine learning",
            "deep learning",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "computer vision",
            "nlp",
            "natural language processing",
            "model training",
            "feature engineering",
        ],
        "llm": [
            "llm",
            "gpt",
            "gemini",
            "openai",
            "instruction tuning",
            "prompt engineering",
            "transformers",
            "retrieval augmented generation",
            "rag",
            "large language model",
        ],
        "retrieval": [
            "vector search",
            "semantic search",
            "elasticsearch",
            "milvus",
            "chromadb",
            "pinecone",
            "faiss",
            "retrieval",
            "search relevance",
        ],
        "ranking": [
            "learning to rank",
            "ranking",
            "relevance model",
            "search ranking",
            "pairwise ranking",
            "recommendation",
        ],
        "mlops": [
            "mlflow",
            "kubeflow",
            "docker",
            "kubernetes",
            "ci/cd",
            "deployment",
            "monitoring",
            "model serving",
            "dataops",
        ],
        "backend": [
            "fastapi",
            "flask",
            "django",
            "rest api",
            "graphql",
            "microservices",
            "python",
            "java",
            "node",
            "api design",
        ],
    }

    STARTUP_TERMS = ["startup", "early stage", "seed", "series a", "series b", "high growth"]
    LEADERSHIP_TERMS = [
        "leadership",
        "mentor",
        "manage",
        "manager",
        "director",
        "head of",
        "vp",
        "principal",
        "architect",
    ]
    GROWTH_TERMS = ["promoted", "promotion", "advanced", "growth", "expanded", "career growth", "progression"]
    AGILITY_TERMS = ["learn", "adapt", "adaptable", "quick learner", "rapidly", "new technology", "pick up"]
    BEHAVIOR_TERMS = ["ownership", "accountable", "responsible", "delivered", "collaborate", "stakeholder", "product", "outcome", "impact"]
    RISK_TERMS = ["contract", "freelance", "consultant", "short-term", "temp", "laid off", "performance issue"]

    COMPANY_SIZE_STARTUP = {"1-10", "11-50", "51-200"}
    COMPANY_SIZE_ENTERPRISE = {"10001+", "5001-10000", "1001-5000"}

    TENURE_PATTERN = re.compile(r"(\d+)\s+(?:years|yrs|year|months|month)", re.IGNORECASE)

    def extract_features(self, candidate: Dict[str, Any]) -> Dict[str, float]:
        """Generate numeric features for a candidate record."""
        profile = candidate.get("profile", {}) or {}
        career_history = candidate.get("career_history", []) or []
        skills = candidate.get("skills", []) or []
        redrob_signals = candidate.get("redrob_signals", {}) or {}
        certifications = candidate.get("certifications", []) or []

        text_corpus = self._build_text_corpus(profile, career_history, skills, certifications)
        skill_names = [self._normalize_text(skill.get("name", "")) for skill in skills]

        technical_scores = self._technical_scores(text_corpus, skill_names, skills)
        career_scores = self._career_scores(profile, career_history, text_corpus)
        behavioral_score = self._behavioral_score(text_corpus, redrob_signals)
        risk_score = self._risk_score(career_scores, redrob_signals, text_corpus)

        return {
            "technical_relevance": technical_scores["technical_relevance"],
            "ai_ml_experience": technical_scores["ai_ml"],
            "llm_experience": technical_scores["llm"],
            "retrieval_experience": technical_scores["retrieval"],
            "ranking_experience": technical_scores["ranking"],
            "mlops_experience": technical_scores["mlops"],
            "backend_experience": technical_scores["backend"],
            "career_growth": career_scores["career_growth"],
            "leadership": career_scores["leadership"],
            "stability": career_scores["stability"],
            "startup_mindset": career_scores["startup_mindset"],
            "learning_agility": career_scores["learning_agility"],
            "behavioral_signals": behavioral_score,
            "risk_indicators": risk_score,
        }

    def _build_text_corpus(
        self,
        profile: Dict[str, Any],
        career_history: List[Dict[str, Any]],
        skills: List[Dict[str, Any]],
        certifications: List[Dict[str, Any]],
    ) -> str:
        """Combine candidate text fields into a normalized corpus for matching."""
        values = [
            profile.get("headline", ""),
            profile.get("summary", ""),
            profile.get("current_title", ""),
            profile.get("current_company", ""),
            profile.get("current_industry", ""),
        ]

        for item in career_history:
            values.extend([
                item.get("company", ""),
                item.get("title", ""),
                item.get("industry", ""),
                item.get("description", ""),
            ])

        values.extend(skill.get("name", "") for skill in skills)
        values.extend(cert.get("name", "") for cert in certifications)
        values.extend(cert.get("issuer", "") for cert in certifications)

        return self._normalize_text(" ".join(values))

    def _technical_scores(
        self, text_corpus: str, skill_names: List[str], skills: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate numeric technical experience features for each bucket."""
        bucket_scores: Dict[str, float] = {}

        for bucket, terms in self.TECHNICAL_BUCKETS.items():
            text_hits = self._count_terms(text_corpus, terms)
            skill_hits = sum(1 for skill_name in skill_names if any(term in skill_name for term in terms))
            duration_score = self._bucket_duration_score(skills, terms)
            bucket_scores[bucket] = self._clamp((text_hits * 0.2) + (skill_hits * 0.2) + (duration_score * 0.6))

        bucket_scores["technical_relevance"] = self._clamp(sum(bucket_scores[b] for b in self.TECHNICAL_BUCKETS) / len(self.TECHNICAL_BUCKETS))
        return bucket_scores

    def _bucket_duration_score(self, skills: List[Dict[str, Any]], terms: List[str]) -> float:
        """Score the bucket based on duration of matched skills."""
        total_months = 0
        for skill in skills:
            name = self._normalize_text(skill.get("name", ""))
            if any(term in name for term in terms):
                total_months += int(skill.get("duration_months", 0) or 0)
        return self._clamp(total_months / 36.0)

    def _career_scores(self, profile: Dict[str, Any], career_history: List[Dict[str, Any]], text_corpus: str) -> Dict[str, float]:
        """Compute career growth, leadership, stability, startup mindset, and learning agility."""
        years_experience = self._coerce_float(profile.get("years_of_experience"), 0.0)
        avg_tenure_months = self._average_tenure_months(career_history)
        role_count = max(1, len(career_history))

        growth_matches = self._count_terms(text_corpus, self.GROWTH_TERMS)
        leadership_matches = self._count_terms(text_corpus, self.LEADERSHIP_TERMS)
        startup_matches = self._count_terms(text_corpus, self.STARTUP_TERMS)
        agility_matches = self._count_terms(text_corpus, self.AGILITY_TERMS)

        growth_score = self._clamp((growth_matches * 0.15) + (leadership_matches * 0.1) + self._normalize_tenure(avg_tenure_months) * 0.4 + min(1.0, years_experience / 10.0) * 0.35)
        leadership_score = self._clamp((leadership_matches * 0.2) + (growth_matches * 0.1) + self._normalize_tenure(avg_tenure_months) * 0.3)
        stability_score = self._compute_stability_score(years_experience, avg_tenure_months, role_count)
        startup_mindset_score = self._clamp((startup_matches * 0.25) + (self._company_startup_signal(profile) * 0.3) + (agility_matches * 0.15))
        learning_agility_score = self._clamp((agility_matches * 0.25) + (growth_matches * 0.15) + (self._bucket_diversity(text_corpus) * 0.35))

        return {
            "career_growth": growth_score,
            "leadership": leadership_score,
            "stability": stability_score,
            "startup_mindset": startup_mindset_score,
            "learning_agility": learning_agility_score,
        }

    def _average_tenure_months(self, career_history: List[Dict[str, Any]]) -> float:
        """Compute the average role tenure in months."""
        months = [int(entry.get("duration_months", 0) or 0) for entry in career_history if isinstance(entry, dict)]
        return sum(months) / len(months) if months else 0.0

    def _normalize_tenure(self, months: float) -> float:
        """Normalize tenure months to a 0-1 scale."""
        return self._clamp(months / 36.0)

    def _compute_stability_score(self, years_experience: float, avg_tenure_months: float, role_count: int) -> float:
        """Estimate stability from tenure and role churn."""
        tenure_score = self._normalize_tenure(avg_tenure_months)
        churn = max(0.0, (role_count - max(1, years_experience)) * 0.1)
        return self._clamp(tenure_score - churn * 0.25 + 0.1)

    def _company_startup_signal(self, profile: Dict[str, Any]) -> float:
        """Score startup-aligned company size and related profile signals."""
        company_size = str(profile.get("current_company_size", "")).lower()
        return 1.0 if company_size in self.COMPANY_SIZE_STARTUP else 0.0

    def _bucket_diversity(self, text_corpus: str) -> float:
        """Measure how many technical buckets appear in the candidate text."""
        present = sum(1 for terms in self.TECHNICAL_BUCKETS.values() if self._count_terms(text_corpus, terms) > 0)
        return self._clamp(present / len(self.TECHNICAL_BUCKETS))

    def _behavioral_score(self, text_corpus: str, redrob_signals: Dict[str, Any]) -> float:
        """Compute a behavioral score from text and engagement features."""
        completeness = self._coerce_float(redrob_signals.get("profile_completeness_score"), 0.0) / 100.0
        recruiter_response = self._coerce_float(redrob_signals.get("recruiter_response_rate"), 0.0)
        interview_completion = self._coerce_float(redrob_signals.get("interview_completion_rate"), 0.0)
        offer_acceptance = self._normalize_offer_acceptance(redrob_signals.get("offer_acceptance_rate", -1.0))
        github_score = self._coerce_float(redrob_signals.get("github_activity_score"), 0.0) / 100.0
        github_score = self._clamp(github_score) if github_score >= 0 else 0.5
        text_matches = self._count_terms(text_corpus, self.BEHAVIOR_TERMS)
        text_score = self._clamp(text_matches / 8.0)

        return self._clamp(
            (0.22 * completeness)
            + (0.18 * recruiter_response)
            + (0.18 * interview_completion)
            + (0.15 * offer_acceptance)
            + (0.12 * github_score)
            + (0.15 * text_score)
        )

    def _normalize_offer_acceptance(self, value: Any) -> float:
        """Normalize offer acceptance rate with -1 treated as missing."""
        try:
            rate = float(value)
        except (TypeError, ValueError):
            return 0.5
        return 0.5 if rate < 0 else self._clamp(rate)

    def _risk_score(self, career_scores: Dict[str, float], redrob_signals: Dict[str, Any], text_corpus: str) -> float:
        """Estimate candidate risk using stability, engagement, and risk keywords."""
        score = 0.0
        stability = career_scores.get("stability", 0.0)
        if stability < 0.4:
            score += 0.25

        completeness = self._coerce_float(redrob_signals.get("profile_completeness_score"), 0.0) / 100.0
        if completeness < 0.5:
            score += 0.15

        recruiter_response = self._coerce_float(redrob_signals.get("recruiter_response_rate"), 0.0)
        if recruiter_response < 0.4:
            score += 0.15

        interview_completion = self._coerce_float(redrob_signals.get("interview_completion_rate"), 0.0)
        if interview_completion < 0.5:
            score += 0.15

        offer_acceptance = self._coerce_float(redrob_signals.get("offer_acceptance_rate", -1.0), -1.0)
        if offer_acceptance <= 0:
            score += 0.1

        avg_response_time = self._coerce_float(redrob_signals.get("avg_response_time_hours"), 0.0)
        if avg_response_time > 72.0:
            score += 0.1

        if self._count_terms(text_corpus, self.RISK_TERMS) > 0:
            score += 0.1

        return self._clamp(score)

    def _count_terms(self, text: str, terms: List[str]) -> int:
        """Count matched keyword terms in normalized text."""
        normalized = self._normalize_text(text)
        return sum(1 for term in terms if term in normalized)

    def _coerce_float(self, value: Any, default: float) -> float:
        """Safely coerce values to float, returning a default on failure."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _normalize_text(self, text: str) -> str:
        """Normalize text for keyword matching."""
        return re.sub(r"\s+", " ", str(text or "")).strip().lower()

    def _clamp(self, value: float) -> float:
        """Clamp a numeric score to the 0-1 range."""
        return max(0.0, min(1.0, value))
