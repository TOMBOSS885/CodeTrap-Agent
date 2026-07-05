def solve(input_data):
    n = input_data["n"]
    edges = input_data.get("edges", [])
    graph = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
    seen = set()
    stack = set()
    def dfs(u):
        seen.add(u)
        stack.add(u)
        for v in graph[u]:
            if v in stack or (v not in seen and dfs(v)):
                return True
        stack.remove(u)
        return False
    if any(dfs(i) for i in range(n) if i not in seen):
        return -1
    return 0

