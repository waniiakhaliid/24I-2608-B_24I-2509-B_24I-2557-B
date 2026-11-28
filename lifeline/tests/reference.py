"""Trusted reference solvers for checking the submitted modules.
Kept in tests/ on purpose: verification code is separate from src/ (Section 7.2).
Deliberately simple and slow; only for small inputs."""


def knapsack_bruteforce(weights, values, capacity, max_n=20):
    """Exact 0/1 knapsack by trying all 2^n subsets. Returns (value, chosen)."""
    n = len(weights)
    if n > max_n:
        raise ValueError(f"brute force limited to n <= {max_n}, got {n}")
    best_v, best_mask = -1, 0
    for mask in range(1 << n):
        w = v = 0
        for i in range(n):
            if (mask >> i) & 1:
                w += weights[i]
                v += values[i]
        if w <= capacity and v > best_v:
            best_v, best_mask = v, mask
    return best_v, [i for i in range(n) if (best_mask >> i) & 1]


def route_bruteforce(penalties, roads, closed, source, max_n=8):
    """Cheapest cost to every location by trying all simple paths. None = unreachable.
    Independent of src (does not use build_graph)."""
    n = len(penalties)
    if n > max_n:
        raise ValueError(f"brute force limited to n <= {max_n}, got {n}")
    arcs = [[] for _ in range(n)]
    for rn, u, v, m in roads:
        if rn in closed:
            continue
        arcs[u].append((v, m + penalties[v]))
        arcs[v].append((u, m + penalties[u]))
    best = [None] * n

    def dfs(u, cost, seen):
        if best[u] is None or cost < best[u]:
            best[u] = cost
        for v, c in arcs[u]:
            if v not in seen:
                dfs(v, cost + c, seen | {v})

    dfs(source, 0, {source})
    return best


def windows_bruteforce(windows, max_n=14):
    """Exact interval scheduling by trying every compatible subset.
    Windows are (id, start, finish, value). Returns (max_count, max_value),
    each maximised independently."""
    n = len(windows)
    if n > max_n:
        raise ValueError(f"brute force limited to n <= {max_n}, got {n}")
    best = [0, 0]

    def rec(i, chosen, count, value):
        if i == n:
            best[0] = max(best[0], count)
            best[1] = max(best[1], value)
            return
        rec(i + 1, chosen, count, value)                       # skip window i
        _, s, f, v = windows[i]
        if all(f <= c[1] or c[2] <= s for c in chosen):        # compatible with all chosen
            rec(i + 1, chosen + [windows[i]], count + 1, value + v)

    rec(0, [], 0, 0)
    return best[0], best[1]


def alarm_reference(alarms):
    """Release schedule by the plain definition: at each tick, take the most urgent alarm among
    those that have arrived (python min over all of them). Returns [(alarm_id, release_tick)].
    Independent of src: no heap, no merge sort."""
    left = list(alarms)
    t, out = 0, []
    while left:
        ready = [a for a in left if a[1] <= t]
        if not ready:
            t = min(a[1] for a in left)
            continue
        best = min(ready, key=lambda a: (-a[2], a[1], a[0]))
        left.remove(best)
        out.append((best[0], t))
        t += 1
    return out