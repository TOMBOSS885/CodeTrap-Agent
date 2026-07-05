from __future__ import annotations

from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = DATA_DIR / "reports"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "codetrap.sqlite3"
SANDBOX_BACKEND = os.getenv("CODETRAP_SANDBOX", "subprocess").strip().lower()
SANDBOX_DOCKER_IMAGE = os.getenv("CODETRAP_DOCKER_IMAGE", "python:3.11-slim")
