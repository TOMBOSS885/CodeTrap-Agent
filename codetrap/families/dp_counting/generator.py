from __future__ import annotations

from codetrap.core.problem import BaseProblemFamily, MutantSolution, ProblemVariant
from codetrap.core.testcase import TestCase

MOD = 1_000_000_007


class DPCountingFamily(BaseProblemFamily):
    family_id = "dp_counting"
    title = "动态规划计数"
    description = "统计满足约束的方案数，结果对 1000000007 取模。"
    input_format = '{"n": 目标台阶, "allowed_steps": [允许步长], "broken": [不可落脚台阶]}'
    output_format = "整数：方案数对 1000000007 取模；非法输入返回 -1"
    difficulty = "medium"
    tags = ["dp", "counting", "modulo"]

    def problem_variants(self) -> list[ProblemVariant]:
        return [
            ProblemVariant("stairs", "损坏楼梯上的爬楼方案", "有一段楼梯编号 0 到 n。你从 0 出发，每次可以走 allowed_steps 中的一种步长，但不能落在 broken 中的台阶上。计算到达 n 的方案数。", ["stairs"]),
            ProblemVariant("robot", "机器人跳格子计数", "机器人从格子 0 跳到格子 n。每次跳跃距离必须来自 allowed_steps，broken 中的格子不可停留。求不同跳跃序列数量。", ["robot"]),
            ProblemVariant("checkpoint", "检查点路径方案", "一条路线有 n 个检查点，允许跨越固定距离前进，部分检查点关闭不可落脚。统计从 0 到 n 的合法前进序列数量。", ["checkpoint"]),
        ]

    def trap_notes(self) -> list[str]:
        return [
            "dp[0] 是初始状态，目标为 0 且起点未损坏时方案数为 1。",
            "broken 中的台阶不能落脚，起点损坏会导致所有方案为 0。",
            "allowed_steps 中的重复步长不应重复贡献。",
            "大输入需要迭代 DP，并在每一步取模。",
        ]

    def reference_solve(self, input_data: dict) -> int:
        n = input_data.get("n")
        steps = input_data.get("allowed_steps", [1, 2])
        broken_raw = input_data.get("broken", [])
        if not isinstance(n, int) or n < 0 or not isinstance(steps, list) or not isinstance(broken_raw, list):
            return -1
        clean_steps = sorted({s for s in steps if isinstance(s, int) and s > 0})
        if not clean_steps:
            return 0
        broken = {x for x in broken_raw if isinstance(x, int)}
        dp = [0] * (n + 1)
        dp[0] = 0 if 0 in broken else 1
        for i in range(1, n + 1):
            if i in broken:
                continue
            dp[i] = sum(dp[i - s] for s in clean_steps if i - s >= 0) % MOD
        return dp[n]

    def generate_cases(self, level: str, count: int) -> list[TestCase]:
        cases = [
            TestCase(id="dp-basic-fib", name="经典 1/2 步", input_data={"n": 5, "allowed_steps": [1, 2], "broken": []}, trap_reason="基础 Fibonacci 转移。", difficulty="basic", tags=["basic"]),
            TestCase(id="dp-basic-three", name="允许三种步长", input_data={"n": 6, "allowed_steps": [1, 3, 4], "broken": []}, trap_reason="多步长转移不能漏项。", difficulty="basic", tags=["multi-step"]),
            TestCase(id="dp-edge-zero", name="目标为 0", input_data={"n": 0, "allowed_steps": [1, 2], "broken": []}, trap_reason="初始空方案应计为 1。", difficulty="edge", tags=["initial-state"]),
            TestCase(id="dp-edge-broken-start", name="起点损坏", input_data={"n": 3, "allowed_steps": [1, 2], "broken": [0]}, trap_reason="起点损坏时没有合法方案。", difficulty="edge", tags=["broken"]),
            TestCase(id="dp-adv-duplicates", name="重复步长和障碍", input_data={"n": 60, "allowed_steps": [1, 2, 2, 3], "broken": [7, 8, 31]}, trap_reason="重复步长不能重复贡献，且要取模。", difficulty="adversarial", tags=["modulo", "dedupe"]),
            TestCase(id="dp-adv-invalid", name="非法 n", input_data={"n": -1, "allowed_steps": [1, 2], "broken": []}, trap_reason="非法输入不能继续计算。", difficulty="adversarial", tags=["validation"]),
        ]
        filtered = [c for c in cases if c.difficulty == level] or cases
        return self._finalize_cases((filtered * ((count // len(filtered)) + 1)), count)

    def reference_solution_code(self) -> str:
        return r'''MOD = 1000000007

def solve(input_data):
    n = input_data.get("n")
    steps = input_data.get("allowed_steps", [1, 2])
    broken_raw = input_data.get("broken", [])
    if not isinstance(n, int) or n < 0 or not isinstance(steps, list) or not isinstance(broken_raw, list):
        return -1
    clean_steps = sorted({s for s in steps if isinstance(s, int) and s > 0})
    if not clean_steps:
        return 0
    broken = {x for x in broken_raw if isinstance(x, int)}
    dp = [0] * (n + 1)
    dp[0] = 0 if 0 in broken else 1
    for i in range(1, n + 1):
        if i in broken:
            continue
        dp[i] = sum(dp[i - s] for s in clean_steps if i - s >= 0) % MOD
    return dp[n]
'''

    def generate_mutants(self) -> list[MutantSolution]:
        return [
            MutantSolution("bad_initial", "初始状态错误", "把 dp[0] 设为 0。", "def solve(input_data):\n    return 0\n"),
            MutantSolution("ignores_broken", "忽略损坏台阶", "允许路径经过 broken。", "def solve(input_data):\n    n=input_data['n']; return n\n"),
            MutantSolution("counts_duplicate_steps", "重复步长重复贡献", "没有去重 allowed_steps。", "def solve(input_data):\n    n=input_data['n']; return n\n"),
        ]
