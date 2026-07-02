"""Job-description intent extraction for recruiter-style ranking."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


DEFAULT_REDROB_JD = """
Job Description: Senior AI Engineer — Founding Team

Company: Redrob AI (Series A AI-native talent intelligence platform)

Location: Pune/Noida, India (Hybrid — flexible cadence) | Open to relocation candidates from Tier-1 Indian cities

Employment Type: Full-time

Experience Required: 5–9 years

What you'd actually be doing:
- Own the intelligence layer of Redrob's product (ranking, retrieval, and matching systems)
- Ship a v2 ranking system with embeddings, hybrid retrieval, and LLM-based re-ranking
- Set up evaluation infrastructure (NDCG, MRR, MAP, A/B testing)

What you absolutely need:
- Production experience with embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5)
- Production experience with vector databases (Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS)
- Strong Python
- Hands-on experience designing evaluation frameworks for ranking systems

What we'd like you to have:
- LLM fine-tuning experience (LoRA, QLoRA, PEFT)
- Experience with learning-to-rank models
- Prior exposure to HR-tech or marketplace products

What we explicitly do NOT want:
- Title-chasers optimizing for Senior/Staff/Principal by switching every 1.5 years
- Framework enthusiasts with only LangChain tutorials
- People who have only worked at consulting firms (TCS, Infosys, Wipro, Accenture)
- People whose primary expertise is computer vision, speech, or robotics without NLP/IR exposure
- Research-only backgrounds without production deployment
- Senior engineers who have not written production code in the last 18 months
- Closed-source-only backgrounds without external validation

Location preferences: Pune/Noida preferred, flexible. Notice period: <30 days preferred.
"""


@dataclass
class JobIntent:
    """Structured representation of what the role actually needs."""

    title: str
    raw_text: str
    required_skills: List[str] = field(default_factory=list)
    optional_skills: List[str] = field(default_factory=list)
    experience_min: Optional[int] = 5
    experience_max: Optional[int] = 9
    behavioral_traits: List[str] = field(default_factory=list)
    primary_locations: List[str] = field(default_factory=lambda: ["pune", "noida"])
    acceptable_locations: List[str] = field(
        default_factory=lambda: ["delhi", "gurgaon", "gurugram", "mumbai", "hyderabad"]
    )
    production_signals: List[str] = field(default_factory=lambda: [
        "production", "deployed", "shipped", "serving", "latency", "a/b test", "ab test",
        "million users", "online-offline", "offline-online", "ndcg", "map@", "mrr",
        "embedding-based", "vector search", "semantic search", "hybrid retrieval",
        "ranking model", "learning to rank", "re-ranking", "reranking", "evaluation framework",
        "information retrieval", "recommendation system", "search system", "retrieval system",
    ])
    anti_patterns: List[str] = field(default_factory=lambda: [
        "pure consulting", "title-chaser", "framework enthusiast", "wrong domain",
        "research-only", "keyword stuffing",
    ])
    core_skill_terms: List[str] = field(default_factory=lambda: [
        "python", "embedding", "retrieval", "vector", "search", "ranking", "ndcg", "map",
        "faiss", "pinecone", "milvus", "weaviate", "qdrant", "opensearch", "elasticsearch",
        "llm", "lora", "qlora", "peft", "rag", "sentence transformer", "bge", "learning to rank",
        "recommendation", "semantic search", "information retrieval", "mlops", "kubernetes",
    ])
    intent_document: str = ""

    @property
    def preferred_locations(self) -> List[str]:
        return [*self.primary_locations, *self.acceptable_locations]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.raw_text,
            "required_skills": self.required_skills,
            "optional_skills": self.optional_skills,
            "experience_min": self.experience_min,
            "experience_max": self.experience_max,
            "behavioral_traits": self.behavioral_traits,
            "primary_locations": self.primary_locations,
            "acceptable_locations": self.acceptable_locations,
            "production_signals": self.production_signals,
            "anti_patterns": self.anti_patterns,
            "core_skill_terms": self.core_skill_terms,
            "intent_document": self.intent_document,
        }


class JobIntentParser:
    """Parse a JD into recruiter-facing intent signals."""

    _SKILL_PATTERNS = {
        "Python": (r"\bpython\b",),
        "embeddings": (r"\bembeddings?\b", r"sentence[- ]transformers?", r"\bbge\b", r"\be5\b"),
        "retrieval": (r"\bretrieval\b", r"information retrieval", r"hybrid search"),
        "ranking systems": (r"\branking\b", r"learning[- ]to[- ]rank", r"\bre-?ranking\b"),
        "vector databases": (
            r"vector database",
            r"\bpinecone\b",
            r"\bweaviate\b",
            r"\bqdrant\b",
            r"\bmilvus\b",
            r"\bfaiss\b",
            r"\bpgvector\b",
        ),
        "search infrastructure": (r"\bopensearch\b", r"\belasticsearch\b", r"hybrid retrieval"),
        "ranking evaluation": (r"\bndcg\b", r"\bmrr\b", r"\bmap\b", r"a/b test", r"evaluation framework"),
        "LLM fine-tuning": (r"fine[- ]tuning", r"\blora\b", r"\bqlora\b", r"\bpeft\b"),
        "MLOps": (r"\bmlops\b", r"model serving", r"model monitoring"),
        "distributed systems": (r"distributed systems", r"large[- ]scale inference"),
        "HR-tech": (r"\bhr[- ]?tech\b", r"recruiting tech", r"talent intelligence"),
        "marketplace products": (r"\bmarketplace\b",),
    }
    _OPTIONAL_SECTION_MARKERS = (
        "things we'd like",
        "what we'd like",
        "nice to have",
        "preferred qualifications",
        "optional skills",
    )
    _NEGATIVE_SECTION_MARKERS = (
        "explicitly do not want",
        "explicitly do not",
        "disqualifiers",
    )

    def parse(self, title: str, description: str) -> JobIntent:
        required_text, optional_text = self._split_skill_sections(description)
        required = self._extract_known_skills(required_text or description)
        optional = [
            skill
            for skill in self._extract_known_skills(optional_text)
            if skill not in required
        ]

        intent = JobIntent(
            title=title or "Senior AI Engineer",
            raw_text=description.strip(),
            required_skills=required,
            optional_skills=optional,
        )
        intent.intent_document = self._build_intent_document(intent)
        return intent

    @classmethod
    def from_text(cls, jd_text: str, title: str = "Senior AI Engineer") -> JobIntent:
        return cls().parse(title, jd_text)

    @classmethod
    def default_redrob(cls) -> JobIntent:
        return cls().parse("Senior AI Engineer — Founding Team", DEFAULT_REDROB_JD)

    def _extract_core_terms(self, text: str) -> List[str]:
        return [skill.lower() for skill in self._extract_known_skills(text)]

    def _extract_known_skills(self, text: str) -> List[str]:
        lowered = text.lower()
        found: List[str] = []
        for canonical, patterns in self._SKILL_PATTERNS.items():
            if any(re.search(pattern, lowered) for pattern in patterns):
                found.append(canonical)
        return found

    def _split_skill_sections(self, text: str) -> tuple[str, str]:
        required_lines: List[str] = []
        optional_lines: List[str] = []
        mode = "required"

        for raw_line in text.splitlines():
            line = raw_line.strip()
            lowered = line.lower().rstrip(":")
            if any(marker in lowered for marker in self._OPTIONAL_SECTION_MARKERS):
                mode = "optional"
                continue
            if any(marker in lowered for marker in self._NEGATIVE_SECTION_MARKERS):
                mode = "negative"
                continue
            if lowered.startswith("things you absolutely need") or lowered.startswith("what you absolutely need"):
                mode = "required"
                continue
            if mode == "required":
                required_lines.append(line)
            elif mode == "optional":
                optional_lines.append(line)

        return "\n".join(required_lines), "\n".join(optional_lines)

    def _build_intent_document(self, intent: JobIntent) -> str:
        parts = [
            intent.title,
            "Role intent: own ranking, retrieval, and matching systems in production.",
            "Must have shipped embeddings, vector search, evaluation for ranking systems.",
            "Strong Python and production ML engineering.",
            f"Required skills: {', '.join(intent.required_skills[:15])}",
            f"Preferred skills: {', '.join(intent.optional_skills[:10])}",
            "Positive signals: product company experience, search/recsys background, A/B testing, NDCG/MAP.",
            "Negative signals: pure consulting, CV/speech-only, framework tutorials, title-chasing, inactive profiles.",
            f"Experience window: {intent.experience_min}-{intent.experience_max} years flexible.",
            f"Primary locations: {', '.join(intent.primary_locations)}.",
            f"Acceptable locations: {', '.join(intent.acceptable_locations)}.",
        ]
        return " ".join(parts)