from __future__ import annotations

from codetrap.core.problem import BaseProblemFamily, MutantSolution
from codetrap.core.testcase import TestCase


class IntervalMergeFamily(BaseProblemFamily):
    family_id = "interval_merge"
    title = "半开区间合并与覆盖判断"
    description = "给定若干半开区间 [start, end)，合并重叠或连续覆盖的区间，计算总覆盖长度，并判断目标区间是否被完全覆盖。"
    input_format = '{"intervals": [[起点, 终点], ...], "target": [目标起点, 目标终点]}'
    output_format = '{"merged": 合并后区间, "covered_length": 覆盖长度, "target_covered": 是否覆盖目标}'
    difficulty = "medium"
    tags = ["interval", "sorting", "coverage"]

    def trap_notes(self) -> list[str]:
        return [
            "本题使用半开区间 [start, end)，空区间应忽略。",
            "输入可能乱序、重复，必须先排序再合并。",
            "相邻半开区间可以形成连续覆盖。",
            "负数边界和大整数边界不能特殊漏掉。",
        ]

    def reference_solve(self, input_data: dict) -> dict:
        intervals = input_data.get("intervals", [])
        target = input_data.get("target")
        if not isinstance(intervals, list):
            return {"error": "invalid"}
        normalized = []
        for item in intervals:
            if not isinstance(item, list) or len(item) != 2 or not all(isinstance(x, int) for x in item):
                return {"error": "invalid"}
            a, b = item
            if a < b:
                normalized.append([a, b])
        normalized.sort()
        merged: list[list[int]] = []
        for a, b in normalized:
            if not merged or a > merged[-1][1]:
                merged.append([a, b])
            else:
                merged[-1][1] = max(merged[-1][1], b)
        covered = sum(b - a for a, b in merged)
        target_covered = False
        if isinstance(target, list) and len(target) == 2 and all(isinstance(x, int) for x in target):
            ta, tb = target
            target_covered = ta >= tb or any(a <= ta and tb <= b for a, b in merged)
        return {"merged": merged, "covered_length": covered, "target_covered": target_covered}

    def generate_cases(self, level: str, count: int) -> list[TestCase]:
        cases = [
            TestCase(id="int-basic-1", name="overlap merge", input_data={"intervals": [[1, 3], [2, 5]], "target": [1, 5]}, trap_reason="Overlapping intervals should merge.", difficulty="basic", tags=["overlap"]),
            TestCase(id="int-edge-1", name="adjacent half open", input_data={"intervals": [[1, 2], [2, 3]], "target": [1, 3]}, trap_reason="Adjacent half-open intervals merge for continuous coverage.", difficulty="edge", tags=["adjacent"]),
            TestCase(id="int-edge-2", name="empty and negative", input_data={"intervals": [[5, 5], [-3, -1], [-2, 2]], "target": [-3, 2]}, trap_reason="Empty intervals are ignored; negative bounds remain valid.", difficulty="edge", tags=["empty", "negative"]),
            TestCase(id="int-adv-1", name="unsorted duplicates", input_data={"intervals": [[10, 20], [1, 4], [1, 4], [3, 10]], "target": [1, 20]}, trap_reason="Input order and duplicates should not affect the merge.", difficulty="adversarial", tags=["sort", "duplicate"]),
        ]
        filtered = [c for c in cases if c.difficulty == level] or cases
        return self._finalize_cases((filtered * ((count // len(filtered)) + 1)), count)

    def generate_mutants(self) -> list[MutantSolution]:
        return [
            MutantSolution("no_sort", "Does not sort intervals", "Merges in input order only.", "def solve(input_data):\n    merged=[]\n    for a,b in input_data['intervals']:\n        if a>=b: continue\n        if not merged or a>merged[-1][1]: merged.append([a,b])\n        else: merged[-1][1]=max(merged[-1][1],b)\n    return {'merged':merged,'covered_length':sum(b-a for a,b in merged),'target_covered':False}\n"),
            MutantSolution("closed_length", "Closed interval length", "Uses b-a+1 length.", "def solve(input_data):\n    return {'merged':input_data['intervals'],'covered_length':sum(b-a+1 for a,b in input_data['intervals'] if a<=b),'target_covered':False}\n"),
            MutantSolution("keeps_empty", "Keeps empty intervals", "Does not drop empty intervals.", "def solve(input_data):\n    return {'merged':sorted(input_data['intervals']),'covered_length':sum(b-a for a,b in input_data['intervals']),'target_covered':False}\n"),
        ]
