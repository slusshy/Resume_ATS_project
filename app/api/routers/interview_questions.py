"""Interview questions API router — generate tailored interview questions per candidate."""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.ranking_repository import RankingRepository

router = APIRouter()


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/{candidate_id}", response_model=Dict[str, List[str]])
async def get_interview_questions(
    candidate_id: int,
    job_description_id: int = Query(..., description="Job description ID for context"),
    session: AsyncSession = Depends(get_session),
):
    """Generate tailored interview questions for a candidate based on their profile and ranking.

    Produces questions across technical, behavioral, leadership, and risk validation categories.
    """
    candidate_repo = CandidateRepository(session)
    ranking_repo = RankingRepository(session)

    # Load candidate
    candidate = await candidate_repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Load ranking to understand strengths/weaknesses
    ranking = await ranking_repo.get_for_candidate_and_job(
        candidate_id=candidate_id,
        job_description_id=job_description_id,
    )

    strengths = []
    weaknesses = []
    risk_level = "Low"

    if ranking and ranking.explanations:
        strengths = ranking.explanations.get("strengths", [])
        weaknesses = ranking.explanations.get("weaknesses", [])
        risk_level = ranking.explanations.get("risk_level", "Low")

    # Generate questions based on profile analysis
    skills = candidate.skills or []
    if skills and isinstance(skills[0], dict):
        skills = [s.get("name", "") for s in skills]

    technical_questions = _generate_technical_questions(skills, strengths, weaknesses)
    behavioral_questions = _generate_behavioral_questions(candidate.name or "Candidate")
    leadership_questions = _generate_leadership_questions()
    risk_validation_questions = _generate_risk_questions(risk_level, weaknesses)

    return {
        "technical_questions": technical_questions,
        "behavioral_questions": behavioral_questions,
        "leadership_questions": leadership_questions,
        "risk_validation_questions": risk_validation_questions,
    }


def _generate_technical_questions(skills: List[str], strengths: List[str],
                                   weaknesses: List[str]) -> List[str]:
    """Generate technical interview questions based on profile."""
    questions = []

    # Questions about demonstrated strengths
    for s in strengths[:3]:
        if "experience" in s.lower() or "skill" in s.lower():
            questions.append(
                f"Your profile shows strong experience in {s.lower()}. "
                "Can you walk us through a challenging project where you applied this?"
            )

    # Questions about weaker areas
    for w in weaknesses[:2]:
        if "experience" in w.lower() or "limited" in w.lower():
            questions.append(
                f"We noticed {w.lower()}. How do you plan to bridge this gap?"
            )

    # Skill-specific questions
    skill_questions = {
        "python": "Describe a production Python application you've built. How did you handle performance, testing, and deployment?",
        "machine learning": "Walk us through an ML project from problem definition to deployment. What metrics did you use?",
        "tensorflow": "How have you optimized TensorFlow models for production inference?",
        "pytorch": "Describe your experience with PyTorch — what's the largest model you've trained?",
        "llm": "How have you integrated LLMs into production systems? Discuss prompt engineering, retrieval augmentation, or fine-tuning.",
        "rag": "How would you design a RAG pipeline for a domain-specific Q&A system?",
        "elasticsearch": "How have you tuned Elasticsearch for relevance and performance at scale?",
        "docker": "Describe your containerization and deployment strategy for ML models.",
        "kubernetes": "How have you orchestrated ML workloads on Kubernetes?",
        "fastapi": "How do you structure a FastAPI application for maintainability and testing?",
        "sql": "Write a query to find the top 5 candidates by overall score grouped by job description.",
    }

    for skill in skills:
        skill_lower = skill.lower()
        for key, question in skill_questions.items():
            if key in skill_lower:
                questions.append(question)
                break

    # Generic fallback questions
    questions.append(
        "Describe a time you had to refactor a large codebase. What approach did you take?"
    )
    questions.append(
        "How do you stay current with emerging technologies in this space?"
    )

    return questions[:8]


def _generate_behavioral_questions(name: str) -> List[str]:
    """Generate behavioral interview questions."""
    return [
        f"{name}, describe a situation where you disagreed with a product or technical decision. How did you handle it?",
        "Tell us about a time you took ownership of a project that was failing or behind schedule.",
        "Describe your approach to collaborating with cross-functional teams (product, design, engineering).",
        "Give an example of a difficult technical decision you made and how you evaluated trade-offs.",
        "How do you handle ambiguity when requirements are unclear or constantly changing?",
        "Describe a time you mentored a junior team member and helped them grow.",
    ]


def _generate_leadership_questions() -> List[str]:
    """Generate leadership assessment questions."""
    return [
        "Describe your experience leading technical projects or initiatives.",
        "How do you balance technical excellence with business constraints and deadlines?",
        "Tell us about a time you influenced technical direction across teams without direct authority.",
        "How do you approach building a culture of code quality, testing, and documentation?",
    ]


def _generate_risk_questions(risk_level: str, weaknesses: List[str]) -> List[str]:
    """Generate risk validation questions based on risk profile."""
    questions = []

    if risk_level in ("Medium", "High"):
        questions.append(
            "Your profile indicates some potential risk areas. How would you address concerns about long-term retention and commitment?"
        )
        questions.append(
            "Can you describe a situation where you left a role earlier than planned and what you learned from it?"
        )

    for w in weaknesses[:3]:
        if "stability" in w.lower() or "tenure" in w.lower():
            questions.append(
                "Your career history shows some shorter tenures. Can you explain the context and what you're looking for in your next role?"
            )

    if not questions:
        questions.append(
            "Everything looks aligned. Is there anything in your background you'd like to clarify or expand on?"
        )

    return questions