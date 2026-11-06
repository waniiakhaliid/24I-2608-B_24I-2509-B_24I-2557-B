"""Module: windows (rescue windows) and incidents (alarm stream)."""
import math
from bisect import bisect_left, bisect_right


def avg_overlap(ws):
    n = len(ws)
    starts, fins = sorted(w[0] for w in ws), sorted(w[1] for w in ws)
    tot = sum(n - 1 - bisect_right(fins, s) - (n - bisect_left(starts, f)) for s, f, _ in ws)
    return tot / n


def _make(rng, n, scale):
    ws = []
    for _ in range(n):
        d = min(480, max(5, int(rng.expovariate(1 / scale)) + 5))
        s = rng.randint(0, 1440 - d)
        ws.append([s, s + d, rng.randint(1, 100)])
    return ws


def _touch(rng, ws, pairs=2):
    used = set()
    n = len(ws)
    for _ in range(pairs):
        a = rng.choice([i for i in range(n) if i not in used and ws[i][1] <= 1400])
        used.add(a)
        b = rng.choice([i for i in range(n) if i not in used])
        used.add(b)
        d = ws[b][1] - ws[b][0]
        ws[b][0] = ws[a][1]
        ws[b][1] = min(1440, ws[b][0] + d)


def gen_windows(rng, n, scen, tier):
    base = {"S": 90, "M": 60, "L": 25, "X": 25}[tier]
    scale = base * (1.5 if scen == 3 and tier == "S" else 1)
    for _ in range(200):
        ws = _make(rng, n, scale)
        _touch(rng, ws)
        if scen != 3 or avg_overlap(ws) >= 2.5:   # every window overlaps >= 2 others on average
            return [tuple(w) for w in ws]
        scale *= 1.2
    raise RuntimeError("window generation failed")


def gen_incidents(rng, A, scen, tier):
    if tier == "S":
        T = rng.randint(max(2, A // 3), A)
    else:
        lo_r, hi_r = (1.55, 1.78) if scen == 4 else (1.25, 1.75)   # alarms per tick in [1.2, 1.8]
        T = rng.randint(math.ceil(A / hi_r), math.floor(A / lo_r))
    bursts = [rng.randint(0, T - 1) for _ in range(rng.randint(3, 6))] if scen == 2 else []
    items = [(0, False), (T - 1, False)]
    for _ in range(A - 2):
        if bursts and rng.random() < 0.6:
            items.append((min(T - 1, rng.choice(bursts) + int(rng.expovariate(1 / 3))), True))
        else:
            items.append((rng.randint(0, T - 1), False))
    items.sort()
    w = [2, 2, 3, 5, 8, 12, 16, 18, 18, 16] if scen == 2 else [8, 10, 12, 14, 14, 12, 10, 8, 6, 6]
    pri = [rng.randint(7, 10) if hot else rng.choices(range(1, 11), weights=w)[0] for _, hot in items]
    forced = rng.sample(range(A), 6)
    vals = [1, 6, 7, 8, 9, 10] if scen == 2 else [1] + rng.sample(range(2, 11), 5)
    for i, v in zip(forced, vals):
        pri[i] = v
    if scen == 2:                                   # mean alarm priority >= 6.0 (aim 6.3)
        fs = set(forced)
        free = [i for i in range(A) if i not in fs]
        while sum(pri) < 6.3 * A:
            i = rng.choice(free)
            pri[i] = max(pri[i], rng.randint(7, 10))
    return [(i + 1, t, p) for i, ((t, _), p) in enumerate(zip(items, pri))]
