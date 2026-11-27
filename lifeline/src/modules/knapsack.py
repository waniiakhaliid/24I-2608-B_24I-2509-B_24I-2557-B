"""Module A: 0/1 knapsack (relief inventory). Written from scratch.

Operation counts (defined in README):
  DP     : table cells computed (sum over crates of W - wi + 1, for wi <= W)
  greedy : key comparisons while sorting + crates examined
  brute  : subsets evaluated
Tie rule (DP): a crate is taken only if it strictly improves the value,
so on equal value the earlier crates are preferred. Deterministic.
"""
import math
from functools import cmp_to_key
from typing import NamedTuple


class KnapsackInputError(ValueError):
    pass


class Result(NamedTuple):
    value: int
    chosen: list      # crate indices (0-based, ascending)
    weight: int
    ops: int


def check_input(weights, values, capacity):
    if len(weights) != len(values):
        raise KnapsackInputError("weights and values differ in length")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
        raise KnapsackInputError(f"capacity must be an integer >= 0, got {capacity!r}")
    for w, v in zip(weights, values):
        if isinstance(w, bool) or not isinstance(w, int) or w <= 0:
            raise KnapsackInputError(f"weight must be a positive integer, got {w!r}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise KnapsackInputError(f"value must be an integer >= 0, got {v!r}")


def _result(weights, values, chosen, ops):
    return Result(sum(values[i] for i in chosen), chosen,
                  sum(weights[i] for i in chosen), ops)


def knapsack_dp(weights, values, capacity):
    """Primary: DP over capacity with traceback. O(nW) time."""
    check_input(weights, values, capacity)
    n = len(weights)
    best = [0] * (capacity + 1)
    keep = []                       # keep[i][w] = 1 if crate i was taken at capacity w
    cells = 0
    for i in range(n):
        wi, vi = weights[i], values[i]
        row = bytearray(capacity + 1)
        for w in range(capacity, wi - 1, -1):   # empty range if wi > capacity
            cand = best[w - wi] + vi
            if cand > best[w]:
                best[w] = cand
                row[w] = 1
        if wi <= capacity:
            cells += capacity - wi + 1
        keep.append(row)
    chosen, w = [], capacity
    for i in range(n - 1, -1, -1):
        if keep[i][w]:
            chosen.append(i)
            w -= weights[i]
    chosen.reverse()
    return _result(weights, values, chosen, cells)


def knapsack_greedy(weights, values, capacity):
    """Baseline: ratio greedy, exact cross-multiplication, skip what does not fit."""
    check_input(weights, values, capacity)
    n = len(weights)
    comps = [0]

    def cmp(a, b):                  # higher value/weight first; ties by index
        comps[0] += 1
        left, right = values[a] * weights[b], values[b] * weights[a]
        if left != right:
            return -1 if left > right else 1
        return (a > b) - (a < b)

    order = sorted(range(n), key=cmp_to_key(cmp))
    load, chosen, examined = 0, [], 0
    for i in order:
        examined += 1
        if load + weights[i] <= capacity:
            load += weights[i]
            chosen.append(i)
    chosen.sort()
    return _result(weights, values, chosen, comps[0] + examined)


def knapsack_bruteforce(weights, values, capacity, max_n=20):
    """Reference: all 2^n subsets. Only for n <= max_n."""
    check_input(weights, values, capacity)
    n = len(weights)
    if n > max_n:
        raise KnapsackInputError(f"brute force limited to n <= {max_n}, got {n}")
    best_v, best_mask = -1, 0
    for mask in range(1 << n):
        w = v = 0
        for i in range(n):
            if (mask >> i) & 1:
                w += weights[i]
                v += values[i]
        if w <= capacity and v > best_v:
            best_v, best_mask = v, mask
    chosen = [i for i in range(n) if (best_mask >> i) & 1]
    return _result(weights, values, chosen, 1 << n)


def crate_arrays(crates_df, multipliers=None):
    """DataFrame of one case -> (weights, values) in crate_id order.
    multipliers: {category: integer factor}; value = floor(base * factor)
    (campaign events: tools x2 on day 2, food x2 on day 3, medicine x3 on day 5)."""
    multipliers = multipliers or {}
    df = crates_df.sort_values("crate_id")
    weights = [int(x) for x in df["weight"]]
    values = [math.floor(int(v) * multipliers.get(int(c), 1))
              for v, c in zip(df["value"], df["cat"])]
    return weights, values