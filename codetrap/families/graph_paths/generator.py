from __future__ import annotations

from collections import deque

from codetrap.core.problem import BaseProblemFamily, MutantSolution
from codetrap.core.testcase import TestCase

MOD = 1_000_000_007


class GraphPathsFamily(BaseProblemFamily):
    family_id = "graph_paths"
    title = "Directed graph path counting"
    description = "Count paths from 0 to n-1 in a directed graph. Return -1 for invalid edges or infinite paths."
    input_format = '{"n": int, "edges": [[u, v], ...]}'
    output_format = "integer path count modulo 1000000007, or -1"
    difficulty = "medium"
    tags = ["graph", "dp", "cycle-detection"]

    def reference_solve(self, input_data: dict) -> int:
        n = input_data.get("n")
        edges = input_data.get("edges", [])
        if not isinstance(n, int) or n <= 0 or not isinstance(edges, list):
            return -1
        graph = [[] for _ in range(n)]
        reverse = [[] for _ in range(n)]
        for edge in edges:
            if not isinstance(edge, list) or len(edge) != 2:
                return -1
            u, v = edge
            if not isinstance(u, int) or not isinstance(v, int) or u < 0 or v < 0 or u >= n or v >= n:
                return -1
            graph[u].append(v)
            reverse[v].append(u)

        reachable = [False] * n
        q = deque([0])
        reachable[0] = True
        while q:
            u = q.popleft()
            for v in graph[u]:
                if not reachable[v]:
                    reachable[v] = True
                    q.append(v)

        can_reach_end = [False] * n
        q = deque([n - 1])
        can_reach_end[n - 1] = True
        while q:
            u = q.popleft()
            for v in reverse[u]:
                if not can_reach_end[v]:
                    can_reach_end[v] = True
                    q.append(v)

        relevant = [reachable[i] and can_reach_end[i] for i in range(n)]
        color = [0] * n

        def has_cycle(u: int) -> bool:
            color[u] = 1
            for v in graph[u]:
                if not relevant[v]:
                    continue
                if color[v] == 1 or (color[v] == 0 and has_cycle(v)):
                    return True
            color[u] = 2
            return False

        for i in range(n):
            if relevant[i] and color[i] == 0 and has_cycle(i):
                return -1

        order: list[int] = []
        seen = [False] * n

        def dfs(u: int) -> None:
            seen[u] = True
            for v in graph[u]:
                if relevant[v] and not seen[v]:
                    dfs(v)
            order.append(u)

        if relevant[0]:
            dfs(0)
        dp = [0] * n
        dp[n - 1] = 1
        for u in order:
            if u == n - 1:
                continue
            dp[u] = sum(dp[v] for v in graph[u] if relevant[v]) % MOD
        return dp[0] if reachable[n - 1] else 0

    def generate_cases(self, level: str, count: int) -> list[TestCase]:
        cases = [
            TestCase(id="graph-basic-1", name="single direct edge", input_data={"n": 2, "edges": [[0, 1]]}, trap_reason="Basic reachability should count one path.", difficulty="basic", tags=["basic"]),
            TestCase(id="graph-basic-2", name="parallel edges", input_data={"n": 3, "edges": [[0, 1], [0, 1], [1, 2]]}, trap_reason="Parallel edges must be counted as distinct choices.", difficulty="basic", tags=["parallel-edge"]),
            TestCase(id="graph-edge-1", name="single node empty path", input_data={"n": 1, "edges": []}, trap_reason="n == 1 counts the empty path.", difficulty="edge", tags=["n1"]),
            TestCase(id="graph-edge-2", name="unreachable target with irrelevant cycle", input_data={"n": 4, "edges": [[0, 1], [2, 2]]}, trap_reason="Cycles outside all source-to-target paths are irrelevant.", difficulty="edge", tags=["irrelevant-cycle"]),
            TestCase(id="graph-adv-1", name="cycle on valid route", input_data={"n": 4, "edges": [[0, 1], [1, 2], [2, 1], [2, 3]]}, trap_reason="Only cycles reachable from source and able to reach target cause infinity.", difficulty="adversarial", tags=["cycle"]),
            TestCase(id="graph-adv-2", name="invalid edge", input_data={"n": 3, "edges": [[0, 3]]}, trap_reason="Invalid edge endpoints must fail with -1.", difficulty="adversarial", tags=["validation"]),
        ]
        filtered = [c for c in cases if c.difficulty == level] or cases
        return self._finalize_cases((filtered * ((count // len(filtered)) + 1)), count)

    def generate_mutants(self) -> list[MutantSolution]:
        return [
            MutantSolution("any_cycle_infinite", "Any cycle means infinite", "Returns -1 when any graph cycle exists, even irrelevant cycles.", "def solve(input_data):\n    n=input_data['n']; edges=input_data.get('edges', [])\n    g=[[] for _ in range(n)]\n    for u,v in edges: g[u].append(v)\n    seen=set(); stack=set()\n    def dfs(u):\n        seen.add(u); stack.add(u)\n        for v in g[u]:\n            if v in stack or (v not in seen and dfs(v)): return True\n        stack.remove(u); return False\n    return -1 if any(dfs(i) for i in range(n) if i not in seen) else 0\n"),
            MutantSolution("dedupe_edges", "Deduplicates edges", "Treats parallel edges as one edge.", "def solve(input_data):\n    n=input_data['n']; edges=list(set(map(tuple,input_data.get('edges',[]))))\n    dp=[0]*n; dp[0]=1\n    for _ in range(n):\n        ndp=dp[:]\n        for u,v in edges: ndp[v]=(ndp[v]+dp[u])%1000000007\n        dp=ndp\n    return dp[n-1]\n"),
            MutantSolution("self_node_zero", "Misses empty path", "Returns 0 for n == 1 without self loop.", "def solve(input_data):\n    if input_data.get('n')==1: return 0\n    return 0\n"),
        ]

