"""Runtime configuration helpers."""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


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
    parsed = urlparse(value)
    if value and parsed.scheme not in {"http", "https"}:
        raise ValueError("base_url must start with http:// or https://")
    host = parsed.hostname or ""
    if not _private_base_urls_allowed() and _is_private_host(host):
        raise ValueError("private or localhost base_url is disabled")


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


def app_password() -> str:
    return os.environ.get("CODETRAP_PASSWORD", "").strip()


def _private_base_urls_allowed() -> bool:
    return os.environ.get("CODETRAP_ALLOW_PRIVATE_BASE_URL", "").strip().lower() in {"1", "true", "yes"}


def _is_private_host(host: str) -> bool:
    if not host:
        return False
    lowered = host.lower()
    if lowered in {"localhost", "host.docker.internal"} or lowered.endswith(".local"):
        return True
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local
