from __future__ import annotations

from codetrap.core.judge_result import JudgeResult
from codetrap.core.problem import ProblemFamily
from codetrap.utils.json_utils import to_pretty_json


def render_markdown_report(family: ProblemFamily, solution_name: str, result: JudgeResult) -> str:
    rate = 0 if result.total_cases == 0 else result.passed_cases / result.total_cases * 100
    lines = [
        "# CodeTrap-Agent Evaluation Report",
        "",
        f"- Problem family: {family.title} (`{family.family_id}`)",
        f"- Candidate file: `{solution_name}`",
        f"- Total cases: {result.total_cases}",
        f"- Passed cases: {result.passed_cases}",
        f"- Failed cases: {len(result.failed_cases)}",
        f"- Pass rate: {rate:.1f}%",
        f"- Runtime: {result.runtime_ms} ms",
        "",
        "## Weakness Summary",
        "",
        result.weakness_summary,
        "",
        "## Failed Cases",
        "",
    ]
    if not result.failed_cases:
        lines.append("No failed cases.")
    for failed in result.failed_cases:
        lines.extend([
            f"### {failed.name} (`{failed.case_id}`)",
            "",
            f"- Error type: `{failed.error_type}`",
            f"- Trap reason: {failed.trap_reason}",
            "",
            "**Input**",
            "```json",
            to_pretty_json(failed.input_data),
            "```",
            "**Expected**",
            "```json",
            to_pretty_json(failed.expected_output),
            "```",
            "**Actual**",
            "```json",
            to_pretty_json(failed.actual_output),
            "```",
        ])
    lines.extend(["", "## Improvement Advice", "", "Review the failed trap categories and add targeted reasoning for boundary validation, state initialization, and operation semantics."])
    return "\n".join(lines)

