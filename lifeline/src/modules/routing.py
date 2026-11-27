"""Module B: route planning. Written from scratch (own binary heap).

Graph: adj[u] = sorted list of (v, step_cost, road_no); roads are two-way,
step cost = minutes + penalty of the destination.

Operation counts (defined in README):
  Dijkstra     : edges examined + heap pushes + heap pops  (heap key comparisons in ops dict)
  Bellman-Ford : relaxations attempted (passes in ops dict)
  BFS          : nodes visited + edges examined
Tie rule: Dijkstra heap key is (cost, node id); a parent changes only on a
strictly cheaper cost, so the first-found route wins ties. BFS visits
neighbours in ascending id.
"""
from typing import NamedTuple

INF = float("inf")


class RoutingInputError(ValueError):
    pass


class MinHeap:
    def __init__(self):
        self.a = []
        self.cmp = 0

    def __len__(self):
        return len(self.a)

    def push(self, item):
        a = self.a
        a.append(item)
        i = len(a) - 1
        while i > 0:
            p = (i - 1) // 2
            self.cmp += 1
            if a[i] < a[p]:
                a[i], a[p] = a[p], a[i]
                i = p
            else:
                break

    def pop(self):
        a = self.a
        top, last = a[0], a.pop()
        if a:
            a[0] = last
            i, n = 0, len(a)
            while True:
                l, r, m = 2 * i + 1, 2 * i + 2, i
                if l < n:
                    self.cmp += 1
                    if a[l] < a[m]:
                        m = l
                if r < n:
                    self.cmp += 1
                    if a[r] < a[m]:
                        m = r
                if m == i:
                    break
                a[i], a[m] = a[m], a[i]
                i = m
        return top


class Paths(NamedTuple):
    dist: list      # cheapest cost per location, None if unreachable
    parent: list    # predecessor, -1 for source/unreachable
    ops: dict


class Reach(NamedTuple):
    hops: list      # fewest roads per location, None if unreachable
    parent: list
    ops: dict


def check_source(adj, source):
    if isinstance(source, bool) or not isinstance(source, int) or not 0 <= source < len(adj):
        raise RoutingInputError(f"source {source!r} is not a location of this map")


def build_graph(penalties, roads, closed=(), storm=False, double_penalty=False):
    """penalties[i] for location i; roads = [(road_no, u, v, minutes)].
    closed: road numbers removed today. storm: minutes x1.5 rounded up.
    double_penalty: penalties >= 2 doubled (dangerous area)."""
    n = len(penalties)
    if n == 0:
        raise RoutingInputError("map has no locations (no HQ)")
    pen = []
    for p in penalties:
        if isinstance(p, bool) or not isinstance(p, int) or p < 0:
            raise RoutingInputError(f"penalty must be an integer >= 0, got {p!r}")
        pen.append(p * 2 if double_penalty and p >= 2 else p)
    closed = set(closed)
    adj = [[] for _ in range(n)]
    for rn, u, v, m in roads:
        if not (0 <= u < n and 0 <= v < n):
            raise RoutingInputError(f"road {rn}: endpoint outside 0..{n - 1}")
        if isinstance(m, bool) or not isinstance(m, int) or m < 1:
            raise RoutingInputError(f"road {rn}: minutes must be an integer >= 1, got {m!r}")
        if rn in closed:
            continue
        if storm:
            m = -(-m * 3 // 2)                      # ceil(1.5 * m), integer arithmetic
        adj[u].append((v, m + pen[v], rn))
        adj[v].append((u, m + pen[u], rn))          # delete this line if roads are one-way
    for lst in adj:
        lst.sort()
    return adj


def dijkstra(adj, source):
    """Primary: heap Dijkstra, cheapest cost from source to every location."""
    check_source(adj, source)
    n = len(adj)
    best, parent, done = [INF] * n, [-1] * n, [False] * n
    best[source] = 0
    heap = MinHeap()
    heap.push((0, source))
    pushes, pops, edges, relax, visited = 1, 0, 0, 0, 0
    while len(heap):
        d, u = heap.pop()
        pops += 1
        if done[u]:
            continue
        done[u] = True
        visited += 1
        for v, c, _ in adj[u]:
            edges += 1
            if d + c < best[v]:
                best[v] = d + c
                parent[v] = u
                heap.push((best[v], v))
                pushes += 1
                relax += 1
    dist = [None if b == INF else b for b in best]
    return Paths(dist, parent, {"total": edges + pushes + pops, "edges": edges, "pushes": pushes,
                                "pops": pops, "relaxations": relax, "visited": visited,
                                "heap_cmp": heap.cmp})


def bellman_ford(adj, source):
    """Baseline: repeated relaxation of every road, stops when a pass changes nothing."""
    check_source(adj, source)
    n = len(adj)
    arcs = [(u, v, c) for u in range(n) for v, c, _ in adj[u]]
    best, parent = [INF] * n, [-1] * n
    best[source] = 0
    attempts = passes = 0
    for _ in range(max(n - 1, 1)):
        changed = False
        passes += 1
        for u, v, c in arcs:
            attempts += 1
            if best[u] != INF and best[u] + c < best[v]:
                best[v] = best[u] + c
                parent[v] = u
                changed = True
        if not changed:
            break
    dist = [None if b == INF else b for b in best]
    return Paths(dist, parent, {"total": attempts, "relaxations": attempts, "passes": passes})


def bfs(adj, source):
    """Reachability and fewest-roads route (neighbours in ascending id)."""
    check_source(adj, source)
    n = len(adj)
    hops, parent = [None] * n, [-1] * n
    hops[source] = 0
    queue, head, edges = [source], 0, 0
    while head < len(queue):
        u = queue[head]
        head += 1
        for v, _, _ in adj[u]:
            edges += 1
            if hops[v] is None:
                hops[v] = hops[u] + 1
                parent[v] = u
                queue.append(v)
    return Reach(hops, parent, {"total": len(queue) + edges, "visited": len(queue), "edges": edges})


def route(parent, reached, source, target):
    """Node list source..target, or None if target is unreachable.
    reached = dist (Dijkstra) or hops (BFS) list."""
    if not 0 <= target < len(parent) or reached[target] is None:
        return None
    path = [target]
    while path[-1] != source:
        path.append(parent[path[-1]])
    path.reverse()
    return path


def walk(adj, path):
    """Cost and road numbers of a node path, using the cheapest parallel road per step."""
    total, roads = 0, []
    for a, b in zip(path, path[1:]):
        steps = [(c, rn) for v, c, rn in adj[a] if v == b]
        if not steps:
            raise RoutingInputError(f"no open road between {a} and {b}")
        c, rn = min(steps)
        total += c
        roads.append(rn)
    return total, roads


# ---- calendar (Section 7.4) -------------------------------------------------
DAY_TARGET = {1: 0, 2: 1, 3: 2, 4: 0, 5: 1, 6: 2, 7: 0}   # index k of target_k
DAY_WAVE = {2: 0, 3: 1, 4: 2, 5: 3}                        # wave i means wave i mod n_waves
STORM_DAYS, DANGER_DAYS, ALL_CLOSED_DAYS = {2}, {4}, {6, 7}


def closed_for_day(waves_df, day):
    """Set of road numbers closed on a day. waves_df has columns wave_no, road_no."""
    if day not in DAY_TARGET:
        raise RoutingInputError(f"day must be 1..7, got {day!r}")
    if len(waves_df) == 0:
        return set()
    if day in ALL_CLOSED_DAYS:
        return {int(r) for r in waves_df["road_no"]}
    if day in DAY_WAVE:
        k = waves_df["wave_no"].nunique()
        w = DAY_WAVE[day] % k
        return {int(r) for r in waves_df[waves_df["wave_no"] == w]["road_no"]}
    return set()


def case_graph(case, day):
    """loader.load_case dict + day -> (adj, target, closed)."""
    loc = case["locations"].sort_values("loc_id")
    pen = [int(p) for p in loc["penalty"]]
    ro = case["roads"]
    roads = [(int(a), int(b), int(c), int(d))
             for a, b, c, d in zip(ro["road_no"], ro["u"], ro["v"], ro["minutes"])]
    closed = closed_for_day(case["waves"], day)
    adj = build_graph(pen, roads, closed, storm=day in STORM_DAYS,
                      double_penalty=day in DANGER_DAYS)
    return adj, int(case["meta"][f"target_{DAY_TARGET[day]}"]), closed