from __future__ import annotations

from codetrap_agent.generator import generate_bundle
from codetrap_agent.mock_data import mock_generation
from codetrap_agent.prompting import build_generation_prompt
from codetrap_agent.schemas import normalize_bundle


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


def test_generate_bundle_persists_state(tmp_path) -> None:
    bundle = generate_bundle(tmp_path, topic="图论", count=1, use_mock=True)
    assert bundle["bundle_id"].startswith("trap_")
    assert (tmp_path / "state.json").exists()
    assert (tmp_path / "raw-responses" / f"{bundle['bundle_id']}.request.json").exists()
