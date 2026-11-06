"""Modules: pipeline, drum, sensors, safety, rations (+ tier-S claims helpers)."""
from bisect import bisect_right


def gen_dims(rng, n):
    return [rng.randint(2, 100) for _ in range(n + 1)]


def gen_drum(rng, L):
    maxp, alpha = rng.randint(150, 500), rng.uniform(0.6, 1.1)
    p = [max(1, min(500, round(maxp * (j / L) ** alpha * rng.uniform(0.85, 1.15)))) for j in range(1, L + 1)]
    if all(p[j - 1] == j * p[0] for j in range(1, L + 1)):  # never proportional to length
        p[-1] += 1 if p[-1] < 500 else -1
    return p


def gen_sensors(rng, n):
    k = rng.randint(2, n // 2)
    cover = sorted(rng.sample(range(n), k))
    cs = set(cover)
    edges = set()
    for x in (x for x in range(n) if x not in cs):
        for c in rng.sample(cover, min(k, rng.randint(1, 2))):
            edges.add(tuple(sorted((x, c))))
    order = cover[:]
    rng.shuffle(order)
    for a, b in zip(order, order[1:]):          # cover nodes form a path -> at least n-1 edges
        edges.add(tuple(sorted((a, b))))
    for _ in range(rng.randint(0, n // 2)):
        c, y = rng.choice(cover), rng.randrange(n)
        if y != c:
            edges.add(tuple(sorted((c, y))))
    return k, cover, sorted(edges)


def rule_count(rng, m, bucket):
    lo, hi = {"low": ((5 * m + 1) // 2, (7 * m + 1) // 2 - 1),       # [2.5, 3.5)
              "mid": ((7 * m + 1) // 2, 24 * m // 5),                 # [3.5, 4.8]
              "high": (24 * m // 5 + 1, 6 * m),                       # (4.8, 6.0]
              "any": (2 * m, 6 * m)}[bucket]
    return rng.randint(lo, hi)


def gen_safety(rng, m, rules):
    planted = [rng.randint(0, 1) for _ in range(m)]
    rows = []
    for _ in range(rules):
        lits = [v if rng.random() < 0.5 else -v for v in rng.sample(range(1, m + 1), 3)]
        if not any((l > 0) == (planted[abs(l) - 1] == 1) for l in lits):
            i = rng.randrange(3)
            lits[i] = -lits[i]                  # flip one false literal -> rule holds for the planted assignment
        rows.append(lits)
    return planted, rows


def gen_rations(rng, n):
    vals = [rng.randint(50, 1000) for _ in range(n)]
    chosen = set(rng.sample(range(n), rng.randint(max(2, n // 4), max(3, n // 2))))
    return vals, [1 if i in chosen else 0 for i in range(n)], sum(vals[i] for i in chosen)


# ----- tier-S exhaustive-search claims -----
def window_opts(ws):
    ws = sorted(ws, key=lambda w: (w[1], w[0]))
    last, cnt = -1, 0
    for s, f, _ in ws:
        if s >= last:
            cnt += 1
            last = f
    fins = [w[1] for w in ws]
    dp = [0] * (len(ws) + 1)
    for i, (s, f, v) in enumerate(ws, 1):
        dp[i] = max(dp[i - 1], dp[bisect_right(fins, s, 0, i - 1)] + v)
    return cnt, dp[-1]


def drum_opt(p):
    L = len(p)
    r = [0] * (L + 1)
    for j in range(1, L + 1):
        r[j] = max(p[i - 1] + r[j - i] for i in range(1, j + 1))
    return r[L]


def min_cover(n, edges):
    em = [(1 << u) | (1 << v) for u, v in edges]
    best = n
    for m in range(1 << n):
        pc = bin(m).count("1")
        if pc < best and all(m & e for e in em):
            best = pc
    return best
