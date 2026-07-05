from __future__ import annotations

from collections import Counter

from codetrap.core.judge_result import FailedCase


def analyze_failures(failed_cases: list[FailedCase]) -> str:
    if not failed_cases:
        return "All generated cases passed. No weakness was detected in this run."
    tags = Counter(tag for case in failed_cases for tag in case.tags)
    reasons = [case.trap_reason for case in failed_cases[:3]]
    tag_text = ", ".join(tag for tag, _ in tags.most_common(5)) or "general correctness"
    return (
        f"The candidate failed {len(failed_cases)} case(s), mainly around {tag_text}. "
        f"Representative traps: {'; '.join(reasons)}"
    )

