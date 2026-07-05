from __future__ import annotations

import json

from codetrap_agent.generator import generate_bundle
from codetrap_agent.mock_data import mock_generation
from codetrap_agent.prompting import build_generation_prompt
from codetrap_agent.schemas import normalize_bundle
from codetrap_agent.config import validate_base_url


def test_prompt_demands_pitfalls_and_tests() -> None:
    prompt = build_generation_prompt("字符串", 2, "Python", "hard")
    assert "pitfalls" in prompt
    assert "至少 8 个" in prompt
    assert "只输出 JSON" in prompt


def test_mock_bundle_normalizes_with_quality() -> None:
    bundle = normalize_bundle(mock_generation("区间", 1), model="mock", topic="区间")
    assert bundle["quality"]["score"] > 0
    assert len(bundle["problems"][0]["tests"]) == 8
    assert len(bundle["problems"][0]["pitfalls"]) == 5
    test = bundle["problems"][0]["tests"][0]
    assert test["input"] == test["kwargs"]
    assert test["output"] == test["expected"]
    assert json.loads(test["input_json"]) == test["kwargs"]
    assert json.loads(test["output_json"]) == test["expected"]
    assert json.loads(test["case_json"]) == {"input": test["kwargs"], "output": test["expected"]}


def test_generate_bundle_persists_state(tmp_path) -> None:
    bundle = generate_bundle(tmp_path, topic="图论", count=1, use_mock=True)
    assert bundle["bundle_id"].startswith("trap_")
    assert (tmp_path / "state.json").exists()
    assert (tmp_path / "raw-responses" / f"{bundle['bundle_id']}.request.json").exists()


def test_private_base_url_is_blocked_by_default() -> None:
    try:
        validate_base_url("http://127.0.0.1:8000/v1")
    except ValueError as exc:
        assert "private" in str(exc)
    else:
        raise AssertionError("private base_url should be blocked by default")
