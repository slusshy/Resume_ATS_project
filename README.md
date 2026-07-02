# RecruiterMind AI

Recruiter-style candidate ranking for the Redrob Intelligent Candidate Discovery challenge.

## Core idea

This project ranks candidates like a strong recruiter — **title + career narrative first**, trusted skills second, platform signals third. It deliberately penalizes keyword-stuffed honeypot profiles (e.g. HR Manager with expert LLM skills).

## Reproduce submission

```bash
pip install -r requirements.txt

python tools/rank_candidates.py --candidates dataset/simple/candidates.jsonl --out submission.csv --no-embeddings

python dataset/simple/validate_submission.py submission.csv
```

## Evaluate on sample set (50 profiles)

```bash
python tools/evaluate_sample.py
python tools/test_pipeline.py
```

## Architecture

```
JD Intent Parser  →  structured role requirements + anti-patterns
        ↓
RecruiterScorer   →  role fit · career coherence · production narrative
                   →  skill trust · honeypot detection · availability
        ↓
submission.csv + API analysis (/analyze/)
```

Unified scoring lives in `app/services/recruiter_scorer.py` and is used by:
- `tools/rank_candidates.py` (hackathon submission)
- `app/services/analysis_service.py` (backend analysis API)

The ranker uses evidence from career descriptions before skill tags, explicitly
scores retrieval/ranking and evaluation depth, applies availability and location
multipliers, and filters high-confidence timeline/profile inconsistencies.

## Run full stack

```bash
uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

Upload structured profiles with `python upload_dataset.py` (backend must be running).

## Scoring components

| Signal | Weight | Purpose |
|--------|--------|---------|
| Role fit | 32% | Title/headline tier (primary anti-honeypot) |
| Production narrative | 24% | Career descriptions citing shipped retrieval/ranking |
| Skill trust | 14% | Duration × endorsements × proficiency |
| Career coherence | 10% | Title aligns with career story |
| Technical features | 8% | Bucketed ML/search experience |
| Behavioral | 7% | Redrob engagement signals |
| Experience fit | 5% | Soft 5–9 year window |

Multipliers: anti-patterns (consulting-only, CV-only), availability, location, honeypot penalty.
