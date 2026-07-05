"""High-level generation workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_runtime_config
from .mock_data import mock_generation
from .model_client import real_completion
from .prompting import build_generation_prompt
from .schemas import normalize_bundle, parse_model_json
from .storage import append_audit, load_state, save_state, write_json


def generate_bundle(
    root: Path,
    *,
    topic: str,
    count: int,
    model: str = "",
    language: str = "Python",
    difficulty: str = "hard",
    use_mock: bool = False,
) -> dict[str, Any]:
    state = load_state(root)
    selected_model = model or _first_model(state)
    prompt = build_generation_prompt(topic, count, language, difficulty)
    if use_mock:
        request_raw = {"mock": True, "prompt": prompt, "model": selected_model or "mock-model"}
        response_raw = {"mock": True, "payload": mock_generation(topic, count)}
        payload = response_raw["payload"]
        selected_model = selected_model or "mock-model"
    else:
        config = load_runtime_config(root, state.get("settings", {}))
        selected_model = selected_model or (config.models[0] if config.models else "")
        result = real_completion(config, selected_model, prompt)
        request_raw = result.request_raw
        response_raw = result.response_raw
        payload = parse_model_json(result.content)
    bundle = normalize_bundle(payload, model=selected_model, topic=topic)
    write_json(root / "raw-responses" / f"{bundle['bundle_id']}.request.json", request_raw)
    write_json(root / "raw-responses" / f"{bundle['bundle_id']}.response.json", response_raw)
    state.setdefault("bundles", []).insert(0, bundle)
    append_audit(state, "bundle.generated", bundle["bundle_id"])
    save_state(root, state)
    return bundle


def export_bundle(root: Path, bundle_id: str) -> Path:
    state = load_state(root)
    bundle = next((item for item in state.get("bundles", []) if item.get("bundle_id") == bundle_id), None)
    if not bundle:
        raise ValueError(f"bundle not found: {bundle_id}")
    output = root / "exports" / f"{bundle_id}.json"
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def _first_model(state: dict[str, Any]) -> str:
    models = state.get("settings", {}).get("models", [])
    return models[0] if models else ""
