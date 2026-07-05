"""Small JSON state store."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .constants import VERSION_TAG


def default_state() -> dict[str, Any]:
    return {
        "schema_version": "codetrap-agent.state.v1",
        "version": VERSION_TAG,
        "settings": {"configured": False, "base_url": "", "api_key_set": False, "models": []},
        "bundles": [],
        "audit": [],
    }


def state_path(root: Path) -> Path:
    return root / "state.json"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def load_state(root: Path) -> dict[str, Any]:
    loaded = read_json(state_path(root), {})
    state = default_state()
    if isinstance(loaded, dict):
        state.update(loaded)
        state["settings"] = {**default_state()["settings"], **loaded.get("settings", {})}
    return state


def save_state(root: Path, state: dict[str, Any]) -> None:
    write_json(state_path(root), state)


def append_audit(state: dict[str, Any], event: str, detail: str) -> None:
    state.setdefault("audit", []).insert(
        0,
        {
            "at": datetime.now(UTC).isoformat(),
            "event": event,
            "detail": detail,
        },
    )
