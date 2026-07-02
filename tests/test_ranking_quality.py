from __future__ import annotations

import unittest

from app.services.jd_intent import DEFAULT_REDROB_JD, JobIntentParser
from app.services.recruiter_scorer import RecruiterScorer


def candidate(
    candidate_id: str,
    *,
    title: str = "Senior Machine Learning Engineer",
    company: str = "Zomato",
    description: str = (
        "Built and deployed a hybrid retrieval and learning-to-rank system in Python. "
        "Owned offline NDCG evaluation and an A/B test before serving 20M queries per month."
    ),
    years: float = 7.0,
    notice: int = 15,
    last_active: str = "2026-05-20",
    open_to_work: bool = True,
    response_rate: float = 0.8,
    start_date: str = "2022-01-01",
    current_roles: int = 1,
) -> dict:
    career = [
        {
            "company": company,
            "title": title,
            "start_date": start_date,
            "end_date": None,
            "duration_months": 53,
            "is_current": True,
            "industry": "Internet",
            "company_size": "1001-5000",
            "description": description,
        }
    ]
    if current_roles > 1:
        career.append({
            **career[0],
            "company": "Second Current Company",
            "start_date": "2024-01-01",
            "duration_months": 29,
        })

    return {
        "candidate_id": candidate_id,
        "profile": {
            "anonymized_name": "Test Candidate",
            "headline": title,
            "summary": description,
            "location": "Noida, Uttar Pradesh",
            "country": "India",
            "years_of_experience": years,
            "current_title": title,
            "current_company": company,
            "current_company_size": "1001-5000",
            "current_industry": "Internet",
        },
        "career_history": career,
        "education": [],
        "skills": [
            {"name": "Python", "proficiency": "expert", "endorsements": 20, "duration_months": 60},
            {"name": "Information Retrieval", "proficiency": "advanced", "endorsements": 12, "duration_months": 48},
            {"name": "Learning to Rank", "proficiency": "advanced", "endorsements": 10, "duration_months": 36},
        ],
        "redrob_signals": {
            "profile_completeness_score": 95,
            "last_active_date": last_active,
            "open_to_work_flag": open_to_work,
            "recruiter_response_rate": response_rate,
            "avg_response_time_hours": 12,
            "skill_assessment_scores": {"Python": 88},
            "notice_period_days": notice,
            "willing_to_relocate": True,
            "github_activity_score": 70,
            "interview_completion_rate": 0.9,
        },
    }


class RankingQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.intent = JobIntentParser.from_text(DEFAULT_REDROB_JD, "Senior AI Engineer")
        cls.scorer = RecruiterScorer(cls.intent, use_embeddings=False, cache_dir=None)

    def test_jd_parser_returns_canonical_skills(self) -> None:
        self.assertIn("Python", self.intent.required_skills)
        self.assertIn("ranking evaluation", self.intent.required_skills)
        self.assertIn("LLM fine-tuning", self.intent.optional_skills)
        self.assertTrue(all(len(skill.split()) <= 3 for skill in self.intent.required_skills))

    def test_evidence_beats_keyword_stuffing(self) -> None:
        strong = self.scorer.score_candidate(candidate("CAND_0000001"))
        stuffer = candidate(
            "CAND_0000002",
            title="Marketing Manager",
            company="Example SaaS",
            description="Managed campaigns, content calendars, and brand partnerships.",
        )
        stuffer["skills"].extend([
            {"name": "Pinecone", "proficiency": "expert", "endorsements": 0, "duration_months": 2},
            {"name": "RAG", "proficiency": "expert", "endorsements": 0, "duration_months": 2},
            {"name": "LLMs", "proficiency": "expert", "endorsements": 0, "duration_months": 2},
        ])
        weak = self.scorer.score_candidate(stuffer)
        self.assertGreater(strong.final_score, weak.final_score)
        self.assertTrue(weak.is_reject_role)

    def test_availability_changes_ranking_materially(self) -> None:
        available = self.scorer.score_candidate(candidate("CAND_0000001"))
        unavailable = self.scorer.score_candidate(candidate(
            "CAND_0000002",
            notice=120,
            last_active="2025-10-01",
            open_to_work=False,
            response_rate=0.1,
        ))
        self.assertGreater(available.availability_multiplier, unavailable.availability_multiplier)
        self.assertGreater(available.final_score, unavailable.final_score * 1.5)

    def test_pre_founding_employment_is_honeypot(self) -> None:
        impossible = candidate(
            "CAND_0000003",
            company="Sarvam AI",
            start_date="2020-01-01",
        )
        result = self.scorer.score_candidate(impossible)
        self.assertTrue(result.is_honeypot)

    def test_ties_are_deterministic(self) -> None:
        higher_id = candidate("CAND_0000010")
        lower_id = candidate("CAND_0000009")
        results, _ = self.scorer.rank_candidates(
            [higher_id, lower_id],
            top_k=2,
            coarse_pool=2,
            progress_every=0,
        )
        self.assertEqual(
            [row["candidate_id"] for row in results],
            ["CAND_0000009", "CAND_0000010"],
        )

    def test_reasoning_is_grounded_and_mentions_major_concern(self) -> None:
        profile = candidate("CAND_0000004", notice=120)
        breakdown = self.scorer.score_candidate(profile)
        reasoning = self.scorer.build_reasoning(profile, breakdown, rank=10)
        self.assertIn("Senior Machine Learning Engineer at Zomato", reasoning)
        self.assertIn("120d", reasoning)
        self.assertLessEqual(len(reasoning.split(".")), 4)


if __name__ == "__main__":
    unittest.main()
