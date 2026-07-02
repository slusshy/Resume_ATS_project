#!/usr/bin/env python3
"""Generate hackathon submission CSV using the unified RecruiterScorer pipeline."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.jd_intent import DEFAULT_REDROB_JD, JobIntentParser
from app.services.recruiter_scorer import RecruiterScorer


def load_candidates(path: Path) -> List[Dict[str, Any]]:
    print(f"Loading candidates from {path}...")
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON candidate file must contain a list of profiles")
        candidates = data
    else:
        candidates = []
        opener = gzip.open if path.suffix.lower() == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    candidates.append(json.loads(line))
    print(f"Loaded {len(candidates)} candidates")
    return candidates


def save_submission(results: List[Dict[str, Any]], output_path: Path) -> None:
    print(f"Saving submission to {output_path}...")
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        for row in results:
            writer.writerow({
                "candidate_id": row["candidate_id"],
                "rank": row["rank"],
                "score": row["score"],
                "reasoning": row["reasoning"],
            })
    print(f"Saved {len(results)} rows")


def validate_results(results: List[Dict[str, Any]], expected_count: int = 100) -> None:
    errors: List[str] = []
    if len(results) != expected_count:
        errors.append(f"expected {expected_count} rows, got {len(results)}")
    ranks = [r["rank"] for r in results]
    if sorted(ranks) != list(range(1, len(results) + 1)):
        errors.append("ranks are not sequential")
    scores = [r["score"] for r in results]
    for i in range(len(scores) - 1):
        if scores[i] < scores[i + 1]:
            errors.append(f"scores increase at rank {ranks[i]} -> {ranks[i + 1]}")
            break
    if len({r["candidate_id"] for r in results}) != len(results):
        errors.append("duplicate candidate IDs")
    for index in range(len(results) - 1):
        current = results[index]
        following = results[index + 1]
        if current["score"] == following["score"] and current["candidate_id"] > following["candidate_id"]:
            errors.append(
                f"rounded score tie is not candidate_id ascending at ranks "
                f"{current['rank']} and {following['rank']}"
            )
            break
    if errors:
        raise ValueError("Invalid ranking output: " + "; ".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser(description="RecruiterMind unified ranking submission generator")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl or sample JSON")
    parser.add_argument("--out", default="submission.csv", help="Output CSV path")
    parser.add_argument("--jd", default=None, help="Optional JD text file")
    parser.add_argument("--cache-dir", default="./cache", help="Embedding cache directory")
    parser.add_argument("--no-embeddings", action="store_true", help="Disable semantic embeddings (faster)")
    parser.add_argument("--top-k", type=int, default=100, help="Number of ranked rows to output")
    parser.add_argument("--coarse-pool", type=int, default=5000, help="Deep-score pool size")
    args = parser.parse_args()

    jd_text = DEFAULT_REDROB_JD
    jd_title = "Senior AI Engineer — Founding Team"
    if args.jd:
        jd_text = Path(args.jd).read_text(encoding="utf-8")
        jd_title = Path(args.jd).stem.replace("_", " ")

    intent = JobIntentParser.from_text(jd_text, jd_title)
    scorer = RecruiterScorer(
        intent,
        use_embeddings=not args.no_embeddings,
        cache_dir=args.cache_dir,
    )

    candidates = load_candidates(Path(args.candidates))
    start = time.time()
    print("\nRunning RecruiterScorer pipeline...")
    results, _ = scorer.rank_candidates(
        candidates,
        top_k=args.top_k,
        coarse_pool=min(args.coarse_pool, len(candidates)),
        progress_every=5000 if len(candidates) > 1000 else 0,
    )
    elapsed = time.time() - start
    print(f"Ranking completed in {elapsed:.1f}s")

    save_submission(results, Path(args.out))
    validate_results(results, expected_count=args.top_k)

    print("\n" + "=" * 60)
    print("SUBMISSION GENERATED")
    print("=" * 60)
    print(f"Output: {args.out}")
    for row in results[:10]:
        print(f"  {row['rank']:3d}. {row['candidate_id']}  score={row['score']:.4f}")
        print(f"       {row['reasoning'][:110]}...")


if __name__ == "__main__":
    main()
