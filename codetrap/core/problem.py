from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from codetrap.core.problem_bundle import ProblemBundle, SearchSource
from codetrap.core.testcase import TestCase


@dataclass(frozen=True)
class MutantSolution:
    id: str
    title: str
    description: str
    code: str


class ProblemFamily(Protocol):
    family_id: str
    title: str
    description: str
    input_format: str
    output_format: str
    difficulty: str
    tags: list[str]

    def generate_cases(self, level: str, count: int) -> list[TestCase]:
        ...

    def reference_solve(self, input_data: dict) -> object:
        ...

    def generate_mutants(self) -> list[MutantSolution]:
        ...

    def statement(self) -> str:
        return self.description

    def reference_solution_code(self) -> str:
        ...

    def generate_problem_bundle(self, level: str, count: int, sources: list[SearchSource], search_query: str, search_status: str) -> ProblemBundle:
        ...


class BaseProblemFamily:
    family_id = ""
    title = ""
    description = ""
    input_format = ""
    output_format = ""
    difficulty = "medium"
    tags: list[str] = []

    def _finalize_cases(self, cases: list[TestCase], count: int) -> list[TestCase]:
        selected = cases[: max(0, count)]
        for case in selected:
            case.expected_output = self.reference_solve(case.input_data)
        return selected

    def statement(self) -> str:
        traps = "\n".join(f"- {item}" for item in self.trap_notes())
        return (
            f"# {self.title}\n\n"
            f"{self.description}\n\n"
            f"## 输入格式\n\n`{self.input_format}`\n\n"
            f"## 输出格式\n\n`{self.output_format}`\n\n"
            f"## 容易让 AI 出错的陷阱\n\n{traps}"
        )

    def trap_notes(self) -> list[str]:
        return [
            "边界条件和非法输入需要明确处理。",
            "测试数据包含基础、边界和对抗样例。",
            "期望输出由 reference_solve 自动计算，避免手写答案不一致。",
        ]

    def reference_solution_code(self) -> str:
        class_name = self.__class__.__name__
        module_name = self.__class__.__module__
        return (
            "from "
            + module_name
            + " import "
            + class_name
            + "\n\n"
            + "def solve(input_data):\n"
            + f"    return {class_name}().reference_solve(input_data)\n"
        )

    def generate_problem_bundle(self, level: str, count: int, sources: list[SearchSource], search_query: str, search_status: str) -> ProblemBundle:
        return ProblemBundle(
            family_id=self.family_id,
            title=self.title,
            statement=self.statement(),
            input_format=self.input_format,
            output_format=self.output_format,
            difficulty=self.difficulty,
            tags=self.tags,
            cases=self.generate_cases(level, count),
            reference_answer=self.reference_solution_code(),
            sources=sources,
            search_query=search_query,
            search_status=search_status,
        )
