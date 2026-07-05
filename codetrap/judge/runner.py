from __future__ import annotations

from pathlib import Path

from codetrap.core.judge_result import FailedCase, JudgeResult
from codetrap.core.problem import ProblemFamily
from codetrap.core.testcase import TestCase
from codetrap.judge.analyzer import analyze_failures
from codetrap.judge.checker import outputs_equal
from codetrap.judge.sandbox import Sandbox, create_sandbox
from codetrap.utils.timing import measure_ms


class JudgeRunner:
    def __init__(self, sandbox: Sandbox | None = None, timeout_sec: float = 2.0) -> None:
        self.sandbox = sandbox or create_sandbox()
        self.timeout_sec = timeout_sec

    def judge(self, family: ProblemFamily, solution_path: str, cases: list[TestCase]) -> JudgeResult:
        failed: list[FailedCase] = []
        with measure_ms() as timer:
            for case in cases:
                expected = case.expected_output
                if expected is None:
                    expected = family.reference_solve(case.input_data)
                run = self.sandbox.run_solution(solution_path, case.input_data, self.timeout_sec)
                if not run.ok:
                    failed.append(FailedCase(case_id=case.id, name=case.name, input_data=case.input_data, expected_output=expected, actual_output=None, error_type=run.error_type or "runtime_error", error_message=run.error_message, trap_reason=case.trap_reason, tags=case.tags))
                elif not outputs_equal(run.output, expected):
                    failed.append(FailedCase(case_id=case.id, name=case.name, input_data=case.input_data, expected_output=expected, actual_output=run.output, error_type="wrong_answer", trap_reason=case.trap_reason, tags=case.tags))
        passed = len(cases) - len(failed)
        return JudgeResult(passed=not failed, total_cases=len(cases), passed_cases=passed, failed_cases=failed, runtime_ms=timer.elapsed_ms, error_type=failed[0].error_type if failed else None, weakness_summary=analyze_failures(failed))


def judge_solution_file(family: ProblemFamily, solution_path: str | Path, cases: list[TestCase]) -> JudgeResult:
    return JudgeRunner().judge(family, str(solution_path), cases)
