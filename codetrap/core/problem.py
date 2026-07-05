from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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
        return self.description

