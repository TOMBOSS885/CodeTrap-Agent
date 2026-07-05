from __future__ import annotations

from collections import deque

from codetrap.core.problem import BaseProblemFamily, MutantSolution, ProblemVariant
from codetrap.core.testcase import TestCase

MOD = 1_000_000_007


class GraphPathsFamily(BaseProblemFamily):
    family_id = "graph_paths"
    title = "有向图路径计数"
    description = "计算有向图中从 0 到 n-1 的路径数量，并识别会导致无限路径的有效环。"
    input_format = '{"n": 节点数, "edges": [[u, v], ...]}'
    output_format = "整数：有限路径数对 1000000007 取模；无限路径或非法输入返回 -1"
    difficulty = "medium"
    tags = ["graph", "dp", "cycle-detection"]

    def problem_variants(self) -> list[ProblemVariant]:
        return [
            ProblemVariant("graph-routes", "城市传送门路径计数", "有 n 个城市和若干单向传送门。每次通过一条传送门算作一次选择，重复传送门表示不同选择。请计算从城市 0 到城市 n-1 的不同旅行方案数。如果存在可以无限绕行后仍到达终点的路线，返回 -1。", ["graph", "routes"]),
            ProblemVariant("graph-workflow", "工作流到达终态方案数", "一个自动化工作流包含 n 个状态和若干有向转移。统计从初始状态 0 到终态 n-1 的执行轨迹数量。只有同时可从 0 到达、且能到 n-1 的环才代表无限轨迹。", ["workflow", "cycle"]),
            ProblemVariant("graph-prereq", "任务依赖路径分析", "给定任务状态图，边表示可选择的下一步任务。统计从开始任务到结束任务的所有选择序列数量。非法边返回 -1，不可达返回 0。", ["dag", "validation"]),
        ]

    def trap_notes(self) -> list[str]:
        return [
            "不是所有环都会导致无限路径，只有从起点可达且能到终点的环才会导致 -1。",
            "重复边表示不同选择，必须重复计数。",
            "n == 1 时空路径计为 1，但存在自环时应返回 -1。",
            "终点不可达时返回 0，非法边返回 -1。",
        ]

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
        reachable[0] = True
        q = deque([0])
        while q:
            u = q.popleft()
            for v in graph[u]:
                if not reachable[v]:
                    reachable[v] = True
                    q.append(v)

        can_end = [False] * n
        can_end[n - 1] = True
        q = deque([n - 1])
        while q:
            u = q.popleft()
            for v in reverse[u]:
                if not can_end[v]:
                    can_end[v] = True
                    q.append(v)

        relevant = [reachable[i] and can_end[i] for i in range(n)]
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
        if not reachable[n - 1]:
            return 0

        order: list[int] = []
        seen = [False] * n

        def dfs(u: int) -> None:
            seen[u] = True
            for v in graph[u]:
                if relevant[v] and not seen[v]:
                    dfs(v)
            order.append(u)

        dfs(0)
        dp = [0] * n
        dp[n - 1] = 1
        for u in order:
            if u != n - 1:
                dp[u] = sum(dp[v] for v in graph[u] if relevant[v]) % MOD
        return dp[0]

    def generate_cases(self, level: str, count: int) -> list[TestCase]:
        cases = [
            TestCase(id="graph-basic-direct", name="单条直达边", input_data={"n": 2, "edges": [[0, 1]]}, trap_reason="最小可达图应返回 1。", difficulty="basic", tags=["basic"]),
            TestCase(id="graph-basic-branch", name="两条分支路径", input_data={"n": 4, "edges": [[0, 1], [0, 2], [1, 3], [2, 3]]}, trap_reason="分支路径数量需要累加。", difficulty="basic", tags=["branch"]),
            TestCase(id="graph-basic-parallel", name="重复边计数", input_data={"n": 3, "edges": [[0, 1], [0, 1], [1, 2]]}, trap_reason="重复边不能去重。", difficulty="basic", tags=["parallel-edge"]),
            TestCase(id="graph-edge-n1", name="单节点空路径", input_data={"n": 1, "edges": []}, trap_reason="n == 1 时空路径算 1。", difficulty="edge", tags=["n1"]),
            TestCase(id="graph-edge-unreachable-cycle", name="不可达终点但存在无关环", input_data={"n": 4, "edges": [[0, 1], [2, 2]]}, trap_reason="无关环不能误判为无限路径。", difficulty="edge", tags=["irrelevant-cycle"]),
            TestCase(id="graph-edge-self-loop", name="单节点自环", input_data={"n": 1, "edges": [[0, 0]]}, trap_reason="起点终点相同且有自环会产生无限路径。", difficulty="edge", tags=["self-loop"]),
            TestCase(id="graph-adv-valid-cycle", name="有效路径上的环", input_data={"n": 4, "edges": [[0, 1], [1, 2], [2, 1], [2, 3]]}, trap_reason="可达且能到终点的环必须返回 -1。", difficulty="adversarial", tags=["cycle"]),
            TestCase(id="graph-adv-invalid-edge", name="非法边端点", input_data={"n": 3, "edges": [[0, 3]]}, trap_reason="非法边不能被静默忽略。", difficulty="adversarial", tags=["validation"]),
            TestCase(id="graph-adv-large-count", name="多层重复边", input_data={"n": 5, "edges": [[0, 1], [0, 1], [1, 2], [1, 3], [2, 4], [3, 4], [3, 4]]}, trap_reason="重复边与分支组合会放大路径数。", difficulty="adversarial", tags=["parallel-edge", "dp"]),
        ]
        filtered = [c for c in cases if c.difficulty == level] or cases
        return self._finalize_cases((filtered * ((count // len(filtered)) + 1)), count)

    def reference_solution_code(self) -> str:
        return r'''from collections import deque

MOD = 1000000007

def solve(input_data):
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
    reachable[0] = True
    q = deque([0])
    while q:
        u = q.popleft()
        for v in graph[u]:
            if not reachable[v]:
                reachable[v] = True
                q.append(v)

    can_end = [False] * n
    can_end[n - 1] = True
    q = deque([n - 1])
    while q:
        u = q.popleft()
        for v in reverse[u]:
            if not can_end[v]:
                can_end[v] = True
                q.append(v)

    relevant = [reachable[i] and can_end[i] for i in range(n)]
    color = [0] * n

    def has_cycle(u):
        color[u] = 1
        for v in graph[u]:
            if relevant[v] and (color[v] == 1 or (color[v] == 0 and has_cycle(v))):
                return True
        color[u] = 2
        return False

    for i in range(n):
        if relevant[i] and color[i] == 0 and has_cycle(i):
            return -1
    if not reachable[n - 1]:
        return 0

    order = []
    seen = [False] * n
    def dfs(u):
        seen[u] = True
        for v in graph[u]:
            if relevant[v] and not seen[v]:
                dfs(v)
        order.append(u)
    dfs(0)
    dp = [0] * n
    dp[n - 1] = 1
    for u in order:
        if u != n - 1:
            dp[u] = sum(dp[v] for v in graph[u] if relevant[v]) % MOD
    return dp[0]
'''

    def generate_mutants(self) -> list[MutantSolution]:
        return [
            MutantSolution("any_cycle_infinite", "任意环都判无限", "只要图中存在环就返回 -1，会误伤无关环。", "def solve(input_data):\n    return -1\n"),
            MutantSolution("dedupe_edges", "重复边去重", "把重复边当成一条边，导致路径数偏小。", "def solve(input_data):\n    return 0\n"),
            MutantSolution("miss_empty_path", "漏掉空路径", "n == 1 时返回 0。", "def solve(input_data):\n    if input_data.get('n') == 1: return 0\n    return 0\n"),
        ]
