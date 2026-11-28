"""Module: network (locations, roads, waves, targets) incl. scenario shapes and trap 48."""
import heapq
import math
from collections import deque
from .common import ceil_pct

PEN = [0, 1, 2, 4, 6]
PEN_W = {1: [15, 15, 25, 25, 20], 2: [25, 25, 20, 15, 15], 3: [30, 25, 20, 15, 10],
         4: [35, 25, 20, 12, 8], 5: [30, 25, 20, 15, 10], 6: [30, 30, 20, 12, 8]}
MIN_RANGE = {1: (5, 40), 2: (15, 60), 3: (3, 45), 4: (1, 25), 5: (10, 60), 6: (1, 20)}
INF = 10 ** 18


# ---------- graph shapes ----------
def pick_E(rng, V, scen):
    maxE = min(3 * V, V * (V - 1) // 2)
    lo, hi = {1: ((11 * V + 9) // 10, (16 * V) // 10),      # avg degree 2.2 .. 3.2
              2: (V, (13 * V) // 10),                       # 2.0 .. 2.6
              3: ((12 * V) // 10, (20 * V) // 10),
              4: ((7 * V + 3) // 4, (26 * V) // 10),        # >= 3.5
              6: ((13 * V) // 10, (22 * V) // 10)}[scen]
    lo = max(lo, V - 1)
    hi = min(hi, maxE)
    return rng.randint(min(lo, hi), hi)


def local_span(scen, V):
    return {1: max(3, math.isqrt(V)), 2: 3, 3: max(4, math.isqrt(V))}.get(scen)


def add_extras(rng, V, es, E, local):
    need = E - len(es)
    if need <= 0:
        return
    if len(es) + need > V * (V - 1) // 4:  # dense: enumerate the missing pairs
        missing = [(a, b) for a in range(V) for b in range(a + 1, V) if (a, b) not in es]
        es.update(rng.sample(missing, need))
        return
    tries = 0
    while need > 0:
        tries += 1
        a = rng.randrange(V)
        b = a + rng.randint(2, local + 3) if (local and tries < 60 * need + 500) else rng.randrange(V)
        if b >= V or a == b:
            continue
        p = (a, b) if a < b else (b, a)
        if p not in es:
            es.add(p)
            need -= 1


def random_graph(rng, V, E, local):
    es = set()
    for i in range(1, V):
        lo = max(0, i - local) if local else 0
        es.add((rng.randint(lo, i - 1), i))      # random spanning tree (connected)
    add_extras(rng, V, es, E, local)
    return sorted(es)


def landslide(rng, V):
    """Single highway (spine) from the HQ with leaf communities, max degree 4, avg degree <= 2.4."""
    P = min(V, max(V // 4 + 2, -(-6 * V // 10)))
    es = {(i, i + 1) for i in range(P - 1)}
    deg = [0] * V
    for a, b in es:
        deg[a] += 1
        deg[b] += 1
    leaves = list(range(P, V))
    for x in leaves:
        s = rng.choice([s for s in range(P) if deg[s] < 4])
        es.add((s, x))
        deg[s] += 1
        deg[x] += 1
    extra = rng.randint(0, max(0, 6 * V // 5 - len(es)))
    tries = 0
    while extra > 0 and tries < 300 and P > 2:
        tries += 1
        a = rng.randrange(0, P - 2)
        b = a + 2
        if (a, b) in es or deg[a] >= 4 or deg[b] >= 4:
            continue
        es.add((a, b))
        deg[a] += 1
        deg[b] += 1
        extra -= 1
    return sorted(es), leaves


# ---------- attributes ----------
def gen_pen(rng, V, scen):
    pen = [rng.choices(PEN, weights=PEN_W[scen])[0] for _ in range(V)]
    pen[0] = 0
    if scen == 1:  # at least 40% of locations with penalty >= 2
        need = ceil_pct(V, 40) + max(1, V // 20)
        cnt = sum(p >= 2 for p in pen)
        low = [i for i in range(1, V) if pen[i] < 2]
        rng.shuffle(low)
        while cnt < need and low:
            pen[low.pop()] = rng.choice([2, 4, 6])
            cnt += 1
    return pen


def assign_types(rng, V, scen, prefer=()):
    nS = max(1, -(-28 * V // 100) + rng.randint(0, V // 8)) if scen == 3 \
        else max(1, round(V * rng.uniform(0.12, 0.22)))
    nH = max(1, round(V * rng.uniform(0.06, 0.12)))
    while nS + nH < 3:
        nS += 1
    nD = min(rng.randint(0, V // 25), V - 1 - nS - nH)
    pre = [x for x in prefer if x != 0]
    ps = set(pre)
    rest = [x for x in range(1, V) if x not in ps]
    rng.shuffle(rest)
    rng.shuffle(pre)
    order = pre + rest
    sh = order[:nS + nH]
    H = set(rng.sample(sh, nH))
    types = ["J"] * V
    types[0] = "D"
    for x in sh:
        types[x] = "H" if x in H else "S"
    for x in order[nS + nH:nS + nH + nD]:
        types[x] = "D"
    return types


def gen_waves(rng, E, scen, forced=None):
    w = rng.randint(3, 5) if scen in (1, 3, 5) else rng.randint(2, 5)
    cap = max(1, E // 4)
    pool = list(range(E))
    rng.shuffle(pool)
    waves, pos = [], 0
    for i in range(w):
        mx = cap if rng.random() < 0.2 else max(1, cap // 2)
        size = max(1, min(rng.randint(1, mx), len(pool) - pos - (w - i - 1)))
        waves.append(pool[pos:pos + size])
        pos += size
    if forced is not None:
        j = rng.randrange(w)
        for i, wv in enumerate(waves):
            if forced in wv:
                wv[wv.index(forced)] = waves[j][0]
                break
        waves[j][0] = forced
    return [sorted(wv) for wv in waves]


# ---------- route analysis ----------
def adjacency(V, edges):
    adj = [[] for _ in range(V)]
    for u, v, m, _ in edges:
        adj[u].append((v, m))
        adj[v].append((u, m))
    return adj


def bfs_hops(V, adj, src=0):
    hop = [-1] * V
    hop[src] = 0
    order = [src]
    dq = deque([src])
    while dq:
        u = dq.popleft()
        for v, _ in adj[u]:
            if hop[v] < 0:
                hop[v] = hop[u] + 1
                order.append(v)
                dq.append(v)
    return hop, order


def route_info(V, adj, pen, src=0):
    """hop distance, cheapest cost, and cheapest cost among fewest-road routes (directed costs)."""
    hop, order = bfs_hops(V, adj, src)
    dist = [INF] * V
    dist[src] = 0
    pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, m in adj[u]:
            nd = d + m + pen[v]
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    fc = [INF] * V
    fc[src] = 0
    for u in order:
        for v, m in adj[u]:
            if hop[v] == hop[u] + 1 and fc[u] + m + pen[v] < fc[v]:
                fc[v] = fc[u] + m + pen[v]
    return hop, dist, fc


def _edge_attrs(rng, scen, pairs):
    lo, hi = MIN_RANGE[scen]
    out = []
    for u, v in pairs:
        m = rng.randint(lo, hi)
        c = max(1, min(100, int(m * rng.uniform(0.8, 2.5)) + rng.randint(0, 20)))
        out.append((u, v, m, c))
    return out


def _relabel(rng, V):
    perm = list(range(1, V))
    rng.shuffle(perm)
    return [0] + perm  # HQ stays 0


def _try(rng, scen, V, need_detour):
    leaves = None
    if scen == 5:
        pairs, leaves = landslide(rng, V)
    else:
        pairs = random_graph(rng, V, pick_E(rng, V, scen), local_span(scen, V))
    mp = _relabel(rng, V)
    pairs = sorted((min(mp[u], mp[v]), max(mp[u], mp[v])) for u, v in pairs)
    if leaves is not None:
        leaves = [mp[x] for x in leaves]
    edges = _edge_attrs(rng, scen, pairs)
    E = len(edges)
    adj = adjacency(V, edges)
    hop, _ = bfs_hops(V, adj)
    if min(hop) < 0:
        return None
    if scen == 5 and max(hop) < V // 4:
        return None
    pen = gen_pen(rng, V, scen)
    types = assign_types(rng, V, scen, prefer=leaves or ())
    SH = [i for i in range(1, V) if types[i] in "SH"]
    forced = None
    if need_detour:
        _, dist, fc = route_info(V, adj, pen)
        cand = [t for t in SH if fc[t] > dist[t]]
        if not cand:
            return None
        t0 = rng.choice(cand)
    elif scen == 5:
        t0 = rng.choice([t for t in leaves if types[t] in "SH"])
    else:
        t0 = rng.choice(SH)
    if scen == 5:  # close the only road into the leaf target: the union of waves cuts it off
        if t0 not in leaves:
            return None
        forced = next(i for i, e in enumerate(edges) if t0 in (e[0], e[1]))
    others = rng.sample([x for x in SH if x != t0], 2)
    targets = [t0] + others
    rng.shuffle(targets)
    waves = gen_waves(rng, E, scen, forced)
    return dict(V=V, edges=edges, pen=pen, types=types, targets=targets, waves=waves)


def make_network(rng, scen, V, need_detour=False):
    for _ in range(500):
        net = _try(rng, scen, V, need_detour)
        if net:
            return net
    raise RuntimeError(f"network generation failed (scenario {scen}, V={V}, detour={need_detour})")


# ---------- trap 48: shortest-looks-cheapest ----------
def make_trap48(rng):
    """HQ -(60 min)- x -(60 min)- T has 2 roads but costs ~126; a chain of h cheap roads reaches T for ~h.
    A 0.7V-long highway hangs off the HQ so that two locations are > 500 roads apart."""
    for _ in range(50):
        V = rng.randint(1500, 3000)
        h = rng.randint(20, 40)
        T = h + 1
        fixed = {(0, 1): 60, (1, T): 60, (0, 2): 1, (h, T): 1}
        pairs = {(0, 1), (1, T), (0, 2), (h, T)}
        for i in range(2, h):
            pairs.add((i, i + 1))
            fixed[(i, i + 1)] = 1
        P = int(0.7 * V)
        spine = list(range(h + 2, h + 2 + P))
        pairs.add((0, spine[0]))
        for a, b in zip(spine, spine[1:]):
            pairs.add((a, b))
        for x in range(h + 2 + P, V):
            pairs.add((rng.choice(spine), x))
        for _c in range(rng.randint(0, V // 30)):
            i = rng.randrange(P - 2)
            pairs.add((spine[i], spine[i + 2]))
        pen = gen_pen(rng, V, 1)
        pen[1] = 6
        for i in range(2, h + 2):
            pen[i] = 0                         # chain nodes and T cost nothing extra
        mp = _relabel(rng, V)
        lo, hi = MIN_RANGE[1]
        edges = []
        for u, v in sorted(pairs):
            m = fixed.get((u, v), rng.randint(lo, hi))
            c = max(1, min(100, int(m * rng.uniform(0.8, 2.5)) + rng.randint(0, 20)))
            a, b = mp[u], mp[v]
            edges.append((min(a, b), max(a, b), m, c))
        edges.sort()
        pen2 = [0] * V
        for i in range(V):
            pen2[mp[i]] = pen[i]
        adj = adjacency(V, edges)
        hop, dist, fc = route_info(V, adj, pen2)
        Tm = mp[T]
        far = max(range(V), key=lambda i: hop[i])
        hop2, _ = bfs_hops(V, adj, far)
        if not (2 * fc[Tm] >= 3 * dist[Tm] and max(hop2) >= 500 and hop[Tm] == 2):
            continue
        types = assign_types(rng, V, 1, prefer=[Tm])
        types[Tm] = "S"
        SH = [i for i in range(1, V) if types[i] in "SH" and i != Tm]
        targets = [Tm] + rng.sample(SH, 2)
        waves = gen_waves(rng, len(edges), 1)
        return dict(V=V, edges=edges, pen=pen2, types=types, targets=targets, waves=waves)
    raise RuntimeError("trap 48 construction failed")
