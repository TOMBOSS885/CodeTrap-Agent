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
LLM_PROVIDER = os.getenv("CODETRAP_LLM_PROVIDER", "none").strip().lower()
LLM_API_KEY = os.getenv("CODETRAP_LLM_API_KEY", "")
LLM_MODEL = os.getenv("CODETRAP_LLM_MODEL", "")
LLM_API_BASE = os.getenv("CODETRAP_LLM_API_BASE", "")
