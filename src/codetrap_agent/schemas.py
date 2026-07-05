"""Validation and normalization for generated trap bundles."""

from __future__ import annotations

import ast
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from .constants import TRAP_DIMENSIONS


class BundleValidationError(ValueError):
    pass


def parse_model_json(content: str) -> dict[str, Any]:
    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        preview = text[:500].replace("\n", "\\n")
        raise BundleValidationError(f"model did not return valid JSON: {exc}; response preview: {preview}") from exc


def normalize_bundle(payload: dict[str, Any], *, model: str, topic: str) -> dict[str, Any]:
    problems = payload.get("problems")
    if not isinstance(problems, list) or not problems:
        raise BundleValidationError("payload.problems must be a non-empty list")
    normalized = {
        "bundle_id": f"trap_{uuid.uuid4().hex[:12]}",
        "schema_version": "codetrap-agent.bundle.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "model": model,
        "topic": topic,
        "problems": [_normalize_problem(item, index) for index, item in enumerate(problems, start=1)],
    }
    normalized["quality"] = score_bundle(normalized)
    return normalized


def score_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    scores = [problem["quality"]["score"] for problem in bundle.get("problems", [])]
    covered = sorted(
        {
            pitfall.get("dimension", "")
            for problem in bundle.get("problems", [])
            for pitfall in problem.get("pitfalls", [])
            if pitfall.get("dimension") in TRAP_DIMENSIONS
        }
    )
    return {
        "score": round(sum(scores) / max(len(scores), 1), 2),
        "covered_dimensions": covered,
        "problem_count": len(bundle.get("problems", [])),
    }


def _normalize_problem(item: Any, index: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise BundleValidationError(f"problem #{index} must be an object")
    required = ["title", "statement", "signature", "reference_solution", "tests", "pitfalls"]
    missing = [key for key in required if not item.get(key)]
    if missing:
        raise BundleValidationError(f"problem #{index} missing fields: {', '.join(missing)}")
    signature = str(item["signature"]).strip()
    _validate_signature(signature, index)
    _validate_reference_solution(str(item["reference_solution"]), index)
    tests = _normalize_tests(item["tests"], index)
    pitfalls = _normalize_pitfalls(item["pitfalls"], tests, index)
    quality = _score_problem(tests, pitfalls, str(item.get("adversarial_notes", "")))
    return {
        "problem_id": f"p{index:03d}_{uuid.uuid4().hex[:8]}",
        "title": str(item["title"]).strip(),
        "topic": str(item.get("topic", "")).strip(),
        "difficulty": str(item.get("difficulty", "")).strip(),
        "statement": str(item["statement"]).strip(),
        "signature": signature,
        "reference_solution": str(item["reference_solution"]).strip() + "\n",
        "tests": tests,
        "pitfalls": pitfalls,
        "adversarial_notes": str(item.get("adversarial_notes", "")).strip(),
        "quality": quality,
    }


def _validate_signature(signature: str, index: int) -> None:
    if not signature.startswith("def ") or not signature.endswith(":"):
        raise BundleValidationError(f"problem #{index} signature must look like a Python def line")
    ast.parse(signature + "\n    pass\n")


def _validate_reference_solution(code: str, index: int) -> None:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise BundleValidationError(f"problem #{index} reference_solution has syntax error") from exc
    if not any(isinstance(node, ast.FunctionDef) for node in tree.body):
        raise BundleValidationError(f"problem #{index} reference_solution must define a function")


def _normalize_tests(values: Any, problem_index: int) -> list[dict[str, Any]]:
    if not isinstance(values, list) or len(values) < 8:
        raise BundleValidationError(f"problem #{problem_index} needs at least 8 tests")
    tests = []
    names = set()
    for index, item in enumerate(values, start=1):
        if not isinstance(item, dict):
            raise BundleValidationError(f"problem #{problem_index} test #{index} must be an object")
        name = str(item.get("name") or f"case_{index}").strip()
        if name in names:
            raise BundleValidationError(f"problem #{problem_index} duplicate test name: {name}")
        names.add(name)
        visibility = str(item.get("visibility", "hidden")).strip()
        if visibility not in {"public", "hidden"}:
            raise BundleValidationError(f"problem #{problem_index} test {name} visibility is invalid")
        kwargs = item.get("kwargs", {})
        if not isinstance(kwargs, dict):
            raise BundleValidationError(f"problem #{problem_index} test {name} kwargs must be an object")
        expected = item.get("expected")
        input_json = _canonical_json({"kwargs": kwargs}, problem_index, name, "input")
        output_json = _canonical_json({"expected": expected}, problem_index, name, "output")
        case_json = _canonical_json(
            {"kwargs": kwargs, "expected": expected},
            problem_index,
            name,
            "case",
        )
        tests.append(
            {
                "name": name,
                "visibility": visibility,
                "input": {"kwargs": kwargs},
                "output": {"expected": expected},
                "kwargs": kwargs,
                "expected": expected,
                "input_json": input_json,
                "output_json": output_json,
                "case_json": case_json,
                "purpose": str(item.get("purpose", "")).strip(),
            }
        )
    public = sum(1 for item in tests if item["visibility"] == "public")
    hidden = sum(1 for item in tests if item["visibility"] == "hidden")
    if public < 3 or hidden < 5:
        raise BundleValidationError(f"problem #{problem_index} needs at least 3 public and 5 hidden tests")
    return tests


def _canonical_json(value: Any, problem_index: int, test_name: str, field: str) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise BundleValidationError(
            f"problem #{problem_index} test {test_name} {field} is not JSON serializable"
        ) from exc


def _normalize_pitfalls(values: Any, tests: list[dict[str, Any]], problem_index: int) -> list[dict[str, Any]]:
    if not isinstance(values, list) or len(values) < 5:
        raise BundleValidationError(f"problem #{problem_index} needs at least 5 pitfalls")
    test_names = {item["name"] for item in tests}
    pitfalls = []
    for index, item in enumerate(values, start=1):
        if not isinstance(item, dict):
            raise BundleValidationError(f"problem #{problem_index} pitfall #{index} must be an object")
        caught_by = item.get("caught_by", [])
        if not isinstance(caught_by, list):
            caught_by = []
        valid_caught_by = [str(name) for name in caught_by if str(name) in test_names]
        pitfalls.append(
            {
                "name": str(item.get("name") or f"pitfall_{index}").strip(),
                "dimension": str(item.get("dimension", "")).strip(),
                "description": str(item.get("description", "")).strip(),
                "likely_wrong_solution": str(item.get("likely_wrong_solution", "")).strip(),
                "caught_by": valid_caught_by,
            }
        )
    return pitfalls


def _score_problem(tests: list[dict[str, Any]], pitfalls: list[dict[str, Any]], notes: str) -> dict[str, Any]:
    dimensions = {item["dimension"] for item in pitfalls if item["dimension"] in TRAP_DIMENSIONS}
    linked = sum(1 for item in pitfalls if item["caught_by"])
    hidden = sum(1 for item in tests if item["visibility"] == "hidden")
    score = 0
    score += min(len(tests), 12) * 4
    score += min(hidden, 8) * 3
    score += min(len(dimensions), 7) * 7
    score += min(linked, len(pitfalls)) * 4
    score += min(len(notes) // 80, 5) * 3
    return {
        "score": min(score, 100),
        "covered_dimensions": sorted(dimensions),
        "linked_pitfalls": linked,
        "hidden_tests": hidden,
    }
