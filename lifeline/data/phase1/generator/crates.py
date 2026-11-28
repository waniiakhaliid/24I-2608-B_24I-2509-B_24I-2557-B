"""Module: crates (+ capacity, greedy/optimal helpers, traps 46 and 47)."""
from fractions import Fraction
from .common import ceil_pct

CAT_WEIGHTS = [30, 25, 20, 15, 10]
# scenario -> (categories counted, minimum percent of crates)
GROUP_RULE = {1: ((0, 1), 55), 2: ((2, 3), 45), 4: ((4,), 10), 6: ((1, 2), 55)}


def _cats(rng, n, scen):
    cats = [rng.choices(range(5), weights=CAT_WEIGHTS)[0] for _ in range(n)]
    if scen in GROUP_RULE:
        grp, pct = GROUP_RULE[scen]
        need = min(n, ceil_pct(n, pct) + rng.randint(0, n // 10))
        for i in rng.sample(range(n), need):
            cats[i] = rng.choice(grp)
    return cats


def _expiry(rng, n, scen):
    if scen == 6:  # supplies spoil: at least half expire by hour 300
        need = min(n, -(-n // 2) + rng.randint(0, n // 5))
        early = set(rng.sample(range(n), need))
        return [rng.randint(0, 300) if i in early else rng.randint(301, 999) for i in range(n)]
    return [rng.randint(0, 999) for _ in range(n)]


def make_crates(rng, n, scen):
    cats, exp = _cats(rng, n, scen), _expiry(rng, n, scen)
    w = [rng.randint(1, 20) for _ in range(n)]
    v = [rng.randint(10, 100) if rng.random() < 0.5 else min(100, max(10, 4 * x + rng.randint(5, 30)))
         for x in w]
    serial = rng.sample(range(10_000_000, 100_000_000), n)
    return [dict(id=i + 1, cat=cats[i], weight=w[i], value=v[i], expiry=exp[i], serial=serial[i])
            for i in range(n)]


def capacity_for(rng, crates):
    tot = sum(c["weight"] for c in crates)
    cap = max(1, -(-tot // 10), int(tot * rng.uniform(0.15, 0.65)))
    return min(cap, (7 * tot) // 10)


def knapsack_opt(crates, cap):
    best = [0] * (cap + 1)
    for c in crates:
        w, v = c["weight"], c["value"]
        for j in range(cap, w - 1, -1):
            if best[j - w] + v > best[j]:
                best[j] = best[j - w] + v
    return best[cap]


def greedy_value(crates, cap):
    """Decreasing exact value/weight (ties: crate_id ascending), skip crates that do not fit."""
    total = left = 0
    left = cap
    for c in sorted(crates, key=lambda c: (-Fraction(c["value"], c["weight"]), c["id"])):
        if c["weight"] <= left:
            left -= c["weight"]
            total += c["value"]
    return total


def dock_order(crates):
    """Trap 46: value, weight, serial ascending and expiry descending in crate_id order."""
    cols = {"value": False, "weight": False, "serial": False, "expiry": True}
    for f, rev in cols.items():
        vals = sorted((c[f] for c in crates), reverse=rev)
        for c, x in zip(crates, vals):
            c[f] = x


def trap47(rng, scen):
    """One light high-ratio 'bait' crate (1 kg, value 10) plus heavy 20 kg crates, capacity 40.
    Greedy takes the bait, then only ONE heavy crate fits; the optimum takes TWO heavy crates."""
    for _ in range(100):
        n = rng.randint(12, 19)
        crates = make_crates(rng, n, scen)
        heavy = [rng.randint(95, 100) for _ in range(n - 1)]
        pos = rng.randrange(n)
        hv = iter(heavy)
        for i, c in enumerate(crates):
            c["weight"], c["value"] = (1, 10) if i == pos else (20, next(hv))
        cap = 40
        tot = sum(c["weight"] for c in crates)
        if 10 * cap >= tot and cap * 10 <= 7 * tot * 10 // 10 and \
                greedy_value(crates, cap) * 100 <= 58 * knapsack_opt(crates, cap):
            return crates, cap
    raise RuntimeError("trap 47 construction failed")
