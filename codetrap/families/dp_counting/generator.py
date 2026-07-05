from __future__ import annotations

from codetrap.core.problem import BaseProblemFamily, MutantSolution
from codetrap.core.testcase import TestCase

MOD = 1_000_000_007


class DPCountingFamily(BaseProblemFamily):
    family_id = "dp_counting"
    title = "带约束的爬楼梯计数"
    description = "给定目标台阶 n、允许的步长集合和损坏台阶列表，计算到达第 n 阶的方案数，结果对 1000000007 取模。"
    input_format = '{"n": 目标台阶, "allowed_steps": 允许步长数组, "broken": 损坏台阶数组}'
    output_format = "整数：方案数对 1000000007 取模"
    difficulty = "medium"
    tags = ["dp", "counting", "modulo"]

    def trap_notes(self) -> list[str]:
        return [
            "dp[0] 是初始状态，目标为 0 时应计为空方案。",
            "broken 中的台阶不能落脚，起点损坏会导致所有路径为 0。",
            "allowed_steps 中的重复步长不应重复贡献。",
            "大规模输入需要迭代 DP 并在每步取模。",
        ]

    def reference_solve(self, input_data: dict) -> int:
        n = input_data.get("n")
        steps = input_data.get("allowed_steps", [1, 2])
        broken = set(input_data.get("broken", []))
        if not isinstance(n, int) or n < 0 or not isinstance(steps, list):
            return -1
        clean_steps = sorted({s for s in steps if isinstance(s, int) and s > 0})
        if not clean_steps:
            return 0
        dp = [0] * (n + 1)
        dp[0] = 0 if 0 in broken else 1
        for i in range(1, n + 1):
            if i in broken:
                continue
            dp[i] = sum(dp[i - s] for s in clean_steps if i - s >= 0) % MOD
        return dp[n]

    def generate_cases(self, level: str, count: int) -> list[TestCase]:
        cases = [
            TestCase(id="dp-basic-1", name="classic stairs", input_data={"n": 5, "allowed_steps": [1, 2], "broken": []}, trap_reason="Basic Fibonacci-style state transition.", difficulty="basic", tags=["basic"]),
            TestCase(id="dp-edge-1", name="zero step target", input_data={"n": 0, "allowed_steps": [1, 2], "broken": []}, trap_reason="Initial state should count one empty plan.", difficulty="edge", tags=["initial-state"]),
            TestCase(id="dp-edge-2", name="broken start", input_data={"n": 3, "allowed_steps": [1, 2], "broken": [0]}, trap_reason="Broken start invalidates every path.", difficulty="edge", tags=["broken"]),
            TestCase(id="dp-adv-1", name="duplicates and large n", input_data={"n": 60, "allowed_steps": [1, 2, 2, 3], "broken": [7, 8, 31]}, trap_reason="Duplicate transitions and modulo placement can skew counts.", difficulty="adversarial", tags=["modulo", "dedupe"]),
        ]
        filtered = [c for c in cases if c.difficulty == level] or cases
        return self._finalize_cases((filtered * ((count // len(filtered)) + 1)), count)

    def generate_mutants(self) -> list[MutantSolution]:
        return [
            MutantSolution("bad_initial", "Bad initial state", "Starts dp[0] at zero.", "def solve(input_data):\n    n=input_data['n']; steps=input_data.get('allowed_steps',[1,2]); dp=[0]*(n+1)\n    for i in range(1,n+1): dp[i]=sum(dp[i-s] for s in steps if i-s>=0)\n    return dp[n]\n"),
            MutantSolution("ignores_broken", "Ignores broken steps", "Counts paths through forbidden steps.", "def solve(input_data):\n    n=input_data['n']; steps=input_data.get('allowed_steps',[1,2]); dp=[0]*(n+1); dp[0]=1\n    for i in range(1,n+1): dp[i]=sum(dp[i-s] for s in steps if i-s>=0)%1000000007\n    return dp[n]\n"),
            MutantSolution("recursive_exponential", "Recursive timeout risk", "Uses naive recursion.", "def solve(input_data):\n    n=input_data['n']; steps=input_data.get('allowed_steps',[1,2])\n    def f(x):\n        if x==0: return 1\n        if x<0: return 0\n        return sum(f(x-s) for s in steps)\n    return f(n)\n"),
        ]
