"""Runtime configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


MASKED_API_KEY = "********"


@dataclass(frozen=True)
class RuntimeConfig:
    base_url: str
    api_key: str
    api_key_set: bool
    models: list[str]


def parse_models(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = value.replace("\n", ",").split(",")
    return [item.strip() for item in raw if item.strip()]


def validate_base_url(value: str) -> None:
    if value and not (value.startswith("http://") or value.startswith("https://")):
        raise ValueError("base_url must start with http:// or https://")


def validate_api_key(value: str) -> None:
    if not value.strip():
        raise ValueError("api_key cannot be empty")


def require_models(models: list[str]) -> None:
    if not models:
        raise ValueError("at least one model is required")


def env_path(root: Path) -> Path:
    return root / ".env"


def load_runtime_config(root: Path, settings: dict | None = None) -> RuntimeConfig:
    settings = settings or {}
    api_key = ""
    path = env_path(root)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("API_KEY="):
                api_key = line.removeprefix("API_KEY=").strip()
                break
    return RuntimeConfig(
        base_url=str(settings.get("base_url", "")),
        api_key=api_key,
        api_key_set=bool(api_key),
        models=list(settings.get("models", [])),
    )


def update_local_api_key(root: Path, api_key: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    env_path(root).write_text(f"API_KEY={api_key.strip()}\n", encoding="utf-8")
