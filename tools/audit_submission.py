#!/usr/bin/env python3
"""Audit a ranking submission for reproducibility and recruiter-quality risks."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.jd_intent import JobIntentParser
from app.services.recruiter_scorer import RecruiterScorer
from tools.rank_candidates import validate_results


def iter_candidates(path: Path) -> Iterable[Dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        yield from data
        return

    opener = gzip.open if path.suffix.lower() == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def load_submission(path: Path) -> list[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    parsed = [
        {
            **row,
            "rank": int(row["rank"]),
            "score": float(row["score"]),
        }
        for row in rows
    ]
    validate_results(parsed, expected_count=100)
    return parsed


def audit(rows: list[Dict[str, Any]], candidates_path: Path) -> tuple[Dict[str, Any], list[str]]:
    selected_ids = {row["candidate_id"] for row in rows}
    candidates = {
        candidate["candidate_id"]: candidate
        for candidate in iter_candidates(candidates_path)
        if candidate.get("candidate_id") in selected_ids
    }
    errors: list[str] = []
    if len(candidates) != len(selected_ids):
        missing = sorted(selected_ids - candidates.keys())
        errors.append(f"{len(missing)} candidate IDs are absent from the dataset")

    scorer = RecruiterScorer(JobIntentParser.default_redrob(), use_embeddings=False, cache_dir=None)
    honeypots = 0
    reject_roles = 0
    retrieval_evidence = 0
    evaluation_evidence = 0
    production_evidence = 0
    long_notice = 0
    grounded_reasoning = 0
    reasonings: list[str] = []

    for row in rows:
        candidate = candidates.get(row["candidate_id"])
        if not candidate:
            continue
        breakdown = scorer.score_candidate(candidate)
        honeypots += int(breakdown.is_honeypot)
        reject_roles += int(breakdown.is_reject_role)
        retrieval_evidence += int(breakdown.retrieval_depth >= 0.45)
        evaluation_evidence += int(breakdown.evaluation_depth >= 0.35)
        production_evidence += int(breakdown.production_narrative >= 0.25)

        redrob = candidate.get("redrob_signals", {}) or {}
        long_notice += int(int(redrob.get("notice_period_days", 0) or 0) > 60)

        profile = candidate.get("profile", {}) or {}
        reasoning = str(row.get("reasoning", "")).strip()
        reasonings.append(reasoning)
        facts = [
            str(profile.get("current_title", "")),
            str(profile.get("current_company", "")),
            str(profile.get("years_of_experience", "")),
        ]
        grounded_reasoning += int(bool(reasoning) and any(fact and fact in reasoning for fact in facts))

    duplicate_reasons = sum(count - 1 for count in Counter(reasonings).values() if count > 1)
    if honeypots:
        errors.append(f"{honeypots} high-confidence honeypot profiles appear in the top 100")
    if reject_roles:
        errors.append(f"{reject_roles} explicit role mismatches appear in the top 100")
    if duplicate_reasons:
        errors.append(f"{duplicate_reasons} duplicate reasoning strings were found")
    if grounded_reasoning < 95:
        errors.append(f"only {grounded_reasoning}/100 reasonings reference a candidate fact")

    report = {
        "rows": len(rows),
        "honeypots": honeypots,
        "reject_roles": reject_roles,
        "retrieval_evidence": retrieval_evidence,
        "evaluation_evidence": evaluation_evidence,
        "production_evidence": production_evidence,
        "long_notice_over_60d": long_notice,
        "grounded_reasoning": grounded_reasoning,
        "duplicate_reasonings": duplicate_reasons,
    }
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    args = parser.parse_args()

    rows = load_submission(args.submission)
    report, errors = audit(rows, args.candidates)
    print(json.dumps(report, indent=2))
    if errors:
        print("\nQuality gate failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("\nQuality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
