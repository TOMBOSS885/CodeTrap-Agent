from __future__ import annotations

from codetrap.core.problem import BaseProblemFamily, MutantSolution, ProblemVariant
from codetrap.core.testcase import TestCase


class IntervalMergeFamily(BaseProblemFamily):
    family_id = "interval_merge"
    title = "半开区间合并与覆盖"
    description = "合并半开区间 [start, end)，计算覆盖长度，并判断目标区间是否被完全覆盖。"
    input_format = '{"intervals": [[start, end], ...], "target": [start, end]}'
    output_format = '{"merged": [[start, end], ...], "covered_length": int, "target_covered": bool}'
    difficulty = "medium"
    tags = ["interval", "sorting", "coverage"]

    def problem_variants(self) -> list[ProblemVariant]:
        return [
            ProblemVariant("calendar", "会议日程覆盖统计", "给定若干会议占用时间段，时间段为半开区间 [start, end)。请合并占用时间，计算总占用时长，并判断目标时间段是否被完全占用。", ["calendar"]),
            ProblemVariant("network-window", "网络维护窗口合并", "系统记录了多个维护窗口。你需要合并重叠或首尾相接的窗口，计算总维护时长，并判断指定窗口是否完全落在维护覆盖内。", ["coverage"]),
            ProblemVariant("sensor-range", "传感器覆盖区间", "一排传感器给出若干半开覆盖区间。请输出合并后的覆盖区间、总覆盖长度，以及目标区间是否被完整覆盖。", ["range"]),
        ]

    def trap_notes(self) -> list[str]:
        return [
            "本题使用半开区间 [start, end)，长度是 end - start。",
            "空区间 start == end 应忽略。",
            "输入可能乱序或重复，必须排序后合并。",
            "相邻区间 [1,2) 和 [2,3) 可以形成连续覆盖。",
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
            TestCase(id="int-basic-overlap", name="重叠区间", input_data={"intervals": [[1, 3], [2, 5]], "target": [1, 5]}, trap_reason="重叠区间应合并。", difficulty="basic", tags=["overlap"]),
            TestCase(id="int-basic-disjoint", name="不相交区间", input_data={"intervals": [[1, 2], [5, 7]], "target": [1, 7]}, trap_reason="不相交区间不能误合并。", difficulty="basic", tags=["disjoint"]),
            TestCase(id="int-edge-adjacent", name="相邻半开区间", input_data={"intervals": [[1, 2], [2, 3]], "target": [1, 3]}, trap_reason="相邻半开区间可连续覆盖。", difficulty="edge", tags=["adjacent"]),
            TestCase(id="int-edge-empty-negative", name="空区间与负数", input_data={"intervals": [[5, 5], [-3, -1], [-2, 2]], "target": [-3, 2]}, trap_reason="空区间忽略，负数边界有效。", difficulty="edge", tags=["empty", "negative"]),
            TestCase(id="int-adv-unsorted-dup", name="乱序重复区间", input_data={"intervals": [[10, 20], [1, 4], [1, 4], [3, 10]], "target": [1, 20]}, trap_reason="必须排序并处理重复。", difficulty="adversarial", tags=["sort", "duplicate"]),
            TestCase(id="int-adv-invalid", name="非法区间", input_data={"intervals": [[1, "x"]], "target": [1, 2]}, trap_reason="非法输入应返回错误。", difficulty="adversarial", tags=["validation"]),
        ]
        filtered = [c for c in cases if c.difficulty == level] or cases
        return self._finalize_cases((filtered * ((count // len(filtered)) + 1)), count)

    def reference_solution_code(self) -> str:
        return r'''def solve(input_data):
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
    merged = []
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
'''

    def generate_mutants(self) -> list[MutantSolution]:
        return [
            MutantSolution("no_sort", "不排序", "按输入顺序合并，乱序时失败。", "def solve(input_data):\n    return {'merged': input_data['intervals'], 'covered_length': 0, 'target_covered': False}\n"),
            MutantSolution("closed_length", "闭区间长度", "错误使用 end-start+1。", "def solve(input_data):\n    return {'merged': input_data['intervals'], 'covered_length': sum(b-a+1 for a,b in input_data['intervals']), 'target_covered': False}\n"),
            MutantSolution("keeps_empty", "保留空区间", "没有忽略 start == end 的区间。", "def solve(input_data):\n    return {'merged': sorted(input_data['intervals']), 'covered_length': 0, 'target_covered': False}\n"),
        ]
