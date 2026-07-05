from __future__ import annotations

from codetrap.core.problem import ProblemFamily
from codetrap.families.dp_counting.generator import DPCountingFamily
from codetrap.families.graph_paths.generator import GraphPathsFamily
from codetrap.families.interval_merge.generator import IntervalMergeFamily
from codetrap.families.json_patch.generator import JsonPatchFamily
from codetrap.families.string_parser.generator import StringParserFamily


class FamilyRegistry:
    def __init__(self) -> None:
        self._families: dict[str, ProblemFamily] = {}

    def register(self, family: ProblemFamily) -> None:
        self._families[family.family_id] = family

    def get(self, family_id: str) -> ProblemFamily:
        if family_id not in self._families:
            raise KeyError(f"unknown problem family: {family_id}")
        return self._families[family_id]

    def all(self) -> list[ProblemFamily]:
        return list(self._families.values())


def build_registry() -> FamilyRegistry:
    registry = FamilyRegistry()
    for family in (
        GraphPathsFamily(),
        JsonPatchFamily(),
        IntervalMergeFamily(),
        StringParserFamily(),
        DPCountingFamily(),
    ):
        registry.register(family)
    return registry


registry = build_registry()

