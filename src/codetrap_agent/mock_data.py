"""Deterministic offline data used for demos and tests."""

from __future__ import annotations

from typing import Any


def mock_generation(topic: str, count: int) -> dict[str, Any]:
    problems = []
    for index in range(1, count + 1):
        problems.append(
            {
                "title": f"{topic} 陷阱题 {index}: 稳定去重窗口",
                "topic": topic,
                "difficulty": "hard",
                "statement": (
                    "实现 solve(items, k)，items 为整数列表，返回所有长度为 k 的连续窗口中，"
                    "按首次出现顺序稳定去重后的字典序最小列表。k 可以为 0；当 k 为 0 时只有空窗口。"
                ),
                "signature": "def solve(items: list[int], k: int) -> list[int]:",
                "reference_solution": (
                    "def solve(items: list[int], k: int) -> list[int]:\n"
                    "    if k < 0 or k > len(items):\n"
                    "        return []\n"
                    "    if k == 0:\n"
                    "        return []\n"
                    "    best = None\n"
                    "    for start in range(0, len(items) - k + 1):\n"
                    "        seen = set()\n"
                    "        cur = []\n"
                    "        for value in items[start:start + k]:\n"
                    "            if value not in seen:\n"
                    "                seen.add(value)\n"
                    "                cur.append(value)\n"
                    "        if best is None or cur < best:\n"
                    "            best = cur\n"
                    "    return best or []\n"
                ),
                "tests": [
                    {"name": "public_basic", "visibility": "public", "kwargs": {"items": [3, 1, 3, 2], "k": 3}, "expected": [1, 3, 2], "purpose": "基本窗口比较"},
                    {"name": "public_all_dup", "visibility": "public", "kwargs": {"items": [2, 2, 2], "k": 2}, "expected": [2], "purpose": "重复元素稳定去重"},
                    {"name": "public_zero", "visibility": "public", "kwargs": {"items": [1, 2], "k": 0}, "expected": [], "purpose": "k 为 0 的定义"},
                    {"name": "hidden_full", "visibility": "hidden", "kwargs": {"items": [2, 1, 2, 1], "k": 4}, "expected": [2, 1], "purpose": "整段窗口"},
                    {"name": "hidden_tie_length", "visibility": "hidden", "kwargs": {"items": [5, 1, 5, 1, 2], "k": 3}, "expected": [1, 5], "purpose": "不要按去重长度贪心"},
                    {"name": "hidden_negative", "visibility": "hidden", "kwargs": {"items": [-1, 0, -1, -2], "k": 3}, "expected": [-1, -2], "purpose": "负数参与字典序"},
                    {"name": "hidden_invalid_large", "visibility": "hidden", "kwargs": {"items": [1], "k": 2}, "expected": [], "purpose": "k 超界"},
                    {"name": "hidden_singleton", "visibility": "hidden", "kwargs": {"items": [9], "k": 1}, "expected": [9], "purpose": "单元素"},
                ],
                "pitfalls": [
                    {"name": "把稳定去重写成排序去重", "dimension": "ordering_stability", "description": "题目要求保留窗口内首次出现顺序，排序会改变语义。", "likely_wrong_solution": "return sorted(set(window))", "caught_by": ["public_basic", "hidden_full"]},
                    {"name": "漏掉 k=0", "dimension": "empty_or_singleton", "description": "很多解法直接枚举窗口导致空窗口语义不明确。", "likely_wrong_solution": "for i in range(len(items)-k+1)", "caught_by": ["public_zero"]},
                    {"name": "窗口右端 off-by-one", "dimension": "off_by_one", "description": "最后一个合法窗口容易漏掉。", "likely_wrong_solution": "range(len(items)-k)", "caught_by": ["hidden_negative"]},
                    {"name": "按去重后长度最小贪心", "dimension": "misleading_greedy", "description": "目标是字典序最小，不是长度最短。", "likely_wrong_solution": "min(candidates, key=len)", "caught_by": ["hidden_tie_length"]},
                    {"name": "k 超界抛异常", "dimension": "ambiguous_boundaries", "description": "超界时应返回空列表而不是切片后继续比较。", "likely_wrong_solution": "best = min(...)", "caught_by": ["hidden_invalid_large"]},
                ],
                "adversarial_notes": "这题把窗口枚举、稳定去重、Python 列表字典序和 k=0/超界语义叠在一起，能补足普通数组题只测 happy path 的不足。",
            }
        )
    return {"problems": problems}
