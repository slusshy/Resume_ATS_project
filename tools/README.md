# Redrob Hackathon - FAST Candidate Ranking System

## ⚡ Quick Start (Fast Version - No Heavy ML Models)

### Step 1: Setup Dataset (First Time Only)

**Windows (Easiest - Double-click):**
```
tools\run_ranking.bat
```

**Or via command line:**
```bash
python tools/setup_dataset.py
```

### Step 2: Generate Submission (FAST!)

**Windows PowerShell:**
```powershell
python tools/rank_candidates_fast.py --candidates "dataset\simple\candidates.jsonl" --out submission.csv
```

**Or double-click:**
```
tools\run_ranking.bat
```

**Expected time:** 2-5 minutes for 100K candidates (with progress indicators!)

### Step 3: Validate Submission

**Windows PowerShell:**
```powershell
python "dataset\simple\validate_submission.py" submission.csv
```

## 🚀 What's Different in Fast Version?

### Original Version (rank_candidates.py)
- ❌ Downloads 1.3GB ML model (BAAI/bge-large-en-v1.5)
- ❌ Downloads 100MB cross-encoder model
- ❌ No progress indicators (looks stuck)
- ❌ Takes 15-20 minutes first run
- ❌ May appear frozen during model download

### Fast Version (rank_candidates_fast.py) ✅
- ✅ No heavy ML models (uses keyword matching + feature engineering)
- ✅ Clear progress indicators every 1000 candidates
- ✅ Completes in 2-5 minutes
- ✅ Shows real-time progress
- ✅ Works immediately without model downloads

## 📊 How It Works

```
1. Load candidates (with progress: "Loaded 1000 candidates...")
   ↓
2. Extract features (with progress: "Processed 5000/100000 candidates")
   ↓
3. Compute scores (fast keyword matching + feature engineering)
   ↓
4. Detect honeypots (penalize impossible profiles)
   ↓
5. Rank and select top 100
   ↓
6. Generate reasoning (specific, varied, honest)
   ↓
7. Save to submission.csv
```

## 🎯 Features Included

### JD-Specific Scoring
- ✅ Experience range (5-9 years: bonus)
- ✅ Location preferences (Pune/Noida: bonus)
- ✅ Notice period (<30 days: bonus)
- ✅ Anti-pattern detection (consulting: penalty)
- ✅ Behavioral signals (response rate, engagement)

### Honeypot Detection
- ✅ Expert in 10+ skills with <2 years experience
- ✅ Multiple "current" roles
- ✅ Timeline inconsistencies

### Reasoning Generation
- ✅ Specific facts from profile
- ✅ JD connection
- ✅ Honest concerns
- ✅ Varied and rank-appropriate

## 📋 Commands Reference

### Setup (One-time)
```bash
python tools/setup_dataset.py
```

### Run Ranking
```bash
python tools/rank_candidates_fast.py --candidates "dataset\simple\candidates.jsonl" --out submission.csv
```

### Validate
```bash
python "dataset\simple\validate_submission.py" submission.csv
```

### Or use batch file (Windows)
```
Double-click: tools\run_ranking.bat
```

## ⚠️ Troubleshooting

### If it still seems slow:
- The script shows progress every 1000 candidates
- For 100K candidates, expect ~2-5 minutes total
- You'll see: "Processed 1000/100000 candidates (5.2s)"

### If you get "module not found" errors:
```bash
pip install -r tools/requirements.txt
```

### If validation fails:
- Check that you have exactly 100 rows
- Check that scores are non-increasing
- Check that all candidate_ids exist

## 🏆 Success Criteria

- ✅ Valid CSV format (passes validate_submission.py)
- ✅ Honeypot rate <10% in top 100
- ✅ Completes in ≤5 minutes
- ✅ Reasoning is present and varied
- ✅ JD-specific scoring applied

## 📞 Need Help?

1. Check progress indicators in console output
2. Ensure dataset/simple/candidates.jsonl exists
3. Run: `python tools/quickstart.py` to verify setup

---

**This fast version prioritizes speed and reliability over maximum accuracy. It will complete quickly and produce a valid submission!** 🚀