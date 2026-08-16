"""Prepare a Python Worker for Cloudflare Workers Builds."""

from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(*command: str) -> None:
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


run("uv", "--version")
run("npm", "ci")
run("uv", "run", "--locked", "pywrangler", "sync")
