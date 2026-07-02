#!/usr/bin/env python3
"""Evaluate ranking quality on the labeled sample candidate set."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.jd_intent import DEFAULT_REDROB_JD, JobIntentParser
from app.services.candidate_utils import normalize_candidate
from app.services.recruiter_scorer import ROLE_REJECT, RecruiterScorer


REJECT_TITLE_FRAGMENTS = ROLE_REJECT


def load_sample(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return [normalize_candidate(c) for c in data]


def is_likely_bad(candidate) -> bool:
    title = (candidate.get("profile", {}).get("current_title") or "").lower()
    return any(frag in title for frag in REJECT_TITLE_FRAGMENTS)


def main():
    base = Path(__file__).parent.parent
    sample_path = base / "dataset/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/sample_candidates.json"
    if not sample_path.exists():
        print(f"Missing sample file: {sample_path}")
        return 1

    candidates = load_sample(sample_path)
    intent = JobIntentParser.from_text(DEFAULT_REDROB_JD, "Senior AI Engineer")
    scorer = RecruiterScorer(intent, use_embeddings=False, cache_dir=str(base / "cache"))

    print("=" * 70)
    print("SAMPLE SET EVALUATION (fast mode, no embeddings)")
    print("=" * 70)

    results, _ = scorer.rank_candidates(candidates, top_k=min(100, len(candidates)), coarse_pool=len(candidates))

    bad_in_top20 = []
    bad_in_top100 = []
    for row in results:
        cid = row["candidate_id"]
        cand = next(c for c in candidates if c["candidate_id"] == cid)
        if is_likely_bad(cand):
            if row["rank"] <= 20:
                bad_in_top20.append(row)
            bad_in_top100.append(row)

    print(f"\nCandidates evaluated: {len(candidates)}")
    print(f"Reject-role profiles in top 20: {len(bad_in_top20)}")
    print(f"Reject-role profiles in top 100: {len(bad_in_top100)}")

    print("\nTop 15:")
    print("-" * 70)
    for row in results[:15]:
        print(f"{row['rank']:3d}. {row['candidate_id']}  score={row['score']:.4f}")
        print(f"     {row['reasoning']}")

    if bad_in_top20:
        print("\nReject-role profiles incorrectly in top 20:")
        for row in bad_in_top20:
            title = next(
                c["profile"]["current_title"] for c in candidates if c["candidate_id"] == row["candidate_id"]
            )
            print(f"  rank {row['rank']}: {row['candidate_id']} ({title})")

    print("\nBottom 5:")
    for row in results[-5:]:
        title = next(c["profile"]["current_title"] for c in candidates if c["candidate_id"] == row["candidate_id"])
        print(f"  rank {row['rank']}: {row['candidate_id']} ({title})")

    return 0 if len(bad_in_top20) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
