from pathlib import Path

from codetrap.core.registry import registry
from codetrap.judge.runner import JudgeRunner
from codetrap.judge.sandbox import DockerSandbox, SubprocessSandbox, create_sandbox


def test_judge_runner_accepts_correct_solution():
    family = registry.get("graph_paths")
    cases = family.generate_cases("basic", 2)
    result = JudgeRunner(timeout_sec=3).judge(family, Path("examples/correct_solution.py").resolve(), cases)
    assert result.passed
    assert result.passed_cases == result.total_cases


def test_judge_runner_rejects_wrong_solution():
    family = registry.get("graph_paths")
    cases = family.generate_cases("edge", 2) + family.generate_cases("adversarial", 1)
    result = JudgeRunner(timeout_sec=3).judge(family, Path("examples/wrong_solution_graph.py").resolve(), cases)
    assert not result.passed
    assert result.failed_cases
    assert "failed" in result.weakness_summary.lower()


def test_sandbox_factory_defaults_to_subprocess():
    assert isinstance(create_sandbox(), SubprocessSandbox)


def test_docker_sandbox_reports_missing_docker_when_unavailable(monkeypatch):
    monkeypatch.setattr("codetrap.judge.sandbox.shutil.which", lambda name: None)
    result = DockerSandbox().run_solution("examples/correct_solution.py", {"n": 1, "edges": []}, 1)
    assert not result.ok
    assert result.error_type == "sandbox_unavailable"
