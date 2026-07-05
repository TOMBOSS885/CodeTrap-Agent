from __future__ import annotations

import random
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


@dataclass(frozen=True)
class ProblemVariant:
    id: str
    title: str
    statement: str
    tags: list[str]


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

    def reference_solution_code(self) -> str:
        ...

    def generate_problem_bundle(
        self,
        level: str,
        count: int,
        sources: list[SearchSource],
        search_query: str,
        search_status: str,
    ) -> ProblemBundle:
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

    def trap_notes(self) -> list[str]:
        return [
            "需要明确处理边界条件和非法输入。",
            "测试数据覆盖基础、边界和对抗样例。",
            "期望输出由 reference_solve 自动计算，避免手写答案不一致。",
        ]

    def problem_variants(self) -> list[ProblemVariant]:
        return [
            ProblemVariant(
                id=f"{self.family_id}-default",
                title=self.title,
                statement=self.description,
                tags=self.tags,
            )
        ]

    def build_statement(self, variant: ProblemVariant) -> str:
        traps = "\n".join(f"- {item}" for item in self.trap_notes())
        return (
            f"# {variant.title}\n\n"
            f"{variant.statement}\n\n"
            f"## 输入格式\n\n`{self.input_format}`\n\n"
            f"## 输出格式\n\n`{self.output_format}`\n\n"
            f"## 容易让 AI 出错的点\n\n{traps}"
        )

    def reference_solution_code(self) -> str:
        raise NotImplementedError("problem family must provide standalone reference_solution_code")

    def generate_problem_bundle(
        self,
        level: str,
        count: int,
        sources: list[SearchSource],
        search_query: str,
        search_status: str,
        variant: ProblemVariant | None = None,
        generation_status: str = "local_variant",
    ) -> ProblemBundle:
        variants = self.problem_variants()
        variant = variant or random.choice(variants)
        cases = self.generate_cases(level, count)
        full_status = search_status if generation_status == "local_variant" else f"{search_status};{generation_status}"
        return ProblemBundle(
            family_id=self.family_id,
            title=variant.title,
            statement=self.build_statement(variant),
            input_format=self.input_format,
            output_format=self.output_format,
            difficulty=self.difficulty,
            tags=sorted(set(self.tags + variant.tags)),
            cases=cases,
            reference_answer=self.reference_solution_code(),
            sources=sources,
            search_query=search_query,
            search_status=full_status,
        )
