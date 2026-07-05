def solve(input_data):
    from collections import deque

    mod = 1_000_000_007
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
    queue = deque([0])
    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if not reachable[v]:
                reachable[v] = True
                queue.append(v)

    can_reach_end = [False] * n
    can_reach_end[n - 1] = True
    queue = deque([n - 1])
    while queue:
        u = queue.popleft()
        for v in reverse[u]:
            if not can_reach_end[v]:
                can_reach_end[v] = True
                queue.append(v)

    relevant = [reachable[i] and can_reach_end[i] for i in range(n)]
    color = [0] * n

    def has_cycle(u):
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
            dp[u] = sum(dp[v] for v in graph[u] if relevant[v]) % mod
    return dp[0]
