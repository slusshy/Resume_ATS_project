#!/usr/bin/env python3
"""Fast ranking mode — same RecruiterScorer logic without embedding model downloads."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    cmd = [
        sys.executable,
        str(root / "rank_candidates.py"),
        *sys.argv[1:],
        "--no-embeddings",
    ]
    if "--candidates" not in sys.argv:
        default = root.parent / "dataset" / "simple" / "candidates.jsonl"
        if default.exists():
            cmd.extend(["--candidates", str(default)])
    if "--out" not in sys.argv:
        cmd.extend(["--out", str(root.parent / "submission.csv")])
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
