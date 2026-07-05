"""Filesystem layout."""

from __future__ import annotations

from pathlib import Path

from .constants import DEFAULT_DATA_DIR


def default_root() -> Path:
    return Path.cwd() / DEFAULT_DATA_DIR


def ensure_tree(root: Path | None = None) -> Path:
    root = root or default_root()
    root.mkdir(parents=True, exist_ok=True)
    for name in ["raw-responses", "exports"]:
        (root / name).mkdir(parents=True, exist_ok=True)
    return root
