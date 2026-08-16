"""Upload a preview Worker version without promoting it to production."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


subprocess.run(
    ["uv", "run", "--locked", "pywrangler", "versions", "upload", *sys.argv[1:]],
    cwd=PROJECT_ROOT,
    check=True,
)
