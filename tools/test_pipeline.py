#!/usr/bin/env python3
"""Test unified ranking pipeline on sample candidates."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.rank_candidates import load_candidates, save_submission, validate_results
from app.services.jd_intent import DEFAULT_REDROB_JD, JobIntentParser
from app.services.recruiter_scorer import RecruiterScorer


def main() -> bool:
    base = Path(__file__).parent.parent
    sample = base / "dataset/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/sample_candidates.json"
    output = base / "test_submission.csv"

    if not sample.exists():
        print(f"ERROR: missing {sample}")
        return False

    intent = JobIntentParser.from_text(DEFAULT_REDROB_JD, "Senior AI Engineer")
    scorer = RecruiterScorer(intent, use_embeddings=False, cache_dir=str(base / "test_cache"))
    candidates = load_candidates(sample)

    print(f"Loaded {len(candidates)} sample candidates")
    results, _ = scorer.rank_candidates(candidates, top_k=min(100, len(candidates)), coarse_pool=len(candidates))

    if len(results) == 0:
        print("ERROR: no eligible candidates ranked")
        return False

    if len(results) < min(100, len(candidates)):
        print(f"NOTE: {len(results)} eligible candidates (honeypots/reject roles excluded)")

    save_submission(results, output)
    validate_results(results)

    print("\nTop 10:")
    for row in results[:10]:
        print(f"  {row['rank']:3d}. {row['candidate_id']}  {row['score']:.4f}")
        print(f"       {row['reasoning'][:100]}")

    print(f"\nSaved to {output}")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
