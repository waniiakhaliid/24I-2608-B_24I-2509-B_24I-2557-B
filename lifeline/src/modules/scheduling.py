"""Module C: rescue scheduling (interval scheduling). Written from scratch (own merge sort).

A window is a tuple (window_id, start, finish, value). Touching windows are compatible
(finish <= next start).

Operation counts (defined in README); preprocessing (sorting) is counted separately:
  sort   : key comparisons + element placements of the merge sort
  EF     : windows examined in the selection pass
  DP     : table cells computed + binary-search steps
  VG     : windows examined + binary-search steps + element shifts on insertion
  total  = sort + select

Tie rules (Section 4.4: every tie is broken by window_id ascending):
  EF / DP sort by (finish, window_id).
  DP takes a window only if it strictly improves the value (zero-value windows are skipped).
  Value-greedy sorts by (value descending, window_id).
"""
from typing import NamedTuple


class SchedulingInputError(ValueError):
    pass


class Result(NamedTuple):
    value: int
    count: int
    chosen: list      # window_ids in time order
    ops: dict


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def check_windows(windows):
    seen = set()
    for w in windows:
        if not isinstance(w, (tuple, list)) or len(w) != 4:
            raise SchedulingInputError(f"window must be (id, start, finish, value), got {w!r}")
        wid, s, f, v = w
        if not all(_is_int(x) for x in w):
            raise SchedulingInputError(f"window fields must be integers, got {w!r}")
        if s < 0:
            raise SchedulingInputError(f"window {wid}: start {s} < 0")
        if f < s:
            raise SchedulingInputError(f"window {wid}: finish {f} before start {s}")
        if v < 0:
            raise SchedulingInputError(f"window {wid}: negative value {v}")
        if wid in seen:
            raise SchedulingInputError(f"duplicate window_id {wid}")
        seen.add(wid)


def merge_sort(items, key):
    """Stable bottom-up merge sort. Returns (sorted list, comparisons, placements)."""
    n = len(items)
    src = [(key(x), x) for x in items]
    comps = moves = 0
    width = 1
    while width < n:
        dst = [None] * n
        for lo in range(0, n, 2 * width):
            mid, hi = min(lo + width, n), min(lo + 2 * width, n)
            i, j, k = lo, mid, lo
            while i < mid and j < hi:
                comps += 1
                if src[j][0] < src[i][0]:
                    dst[k] = src[j]
                    j += 1
                else:
                    dst[k] = src[i]
                    i += 1
                k += 1
                moves += 1
            while i < mid:
                dst[k] = src[i]
                i += 1
                k += 1
                moves += 1
            while j < hi:
                dst[k] = src[j]
                j += 1
                k += 1
                moves += 1
        src = dst
        width *= 2
    return [x for _, x in src], comps, moves


def _count_le(arr, x, hi):
    """Number of elements of arr[0:hi] that are <= x (arr ascending). Returns (count, steps)."""
    lo, steps = 0, 0
    while lo < hi:
        steps += 1
        mid = (lo + hi) // 2
        if arr[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo, steps


def _ops(sort_cmp, sort_moves, select, **extra):
    d = {"total": sort_cmp + sort_moves + select, "sort": sort_cmp + sort_moves,
         "select": select, "sort_cmp": sort_cmp, "sort_moves": sort_moves}
    d.update(extra)
    return d


def earliest_finish(windows):
    """Primary (count): earliest-finish greedy. Maximises the number of windows."""
    check_windows(windows)
    order, c, m = merge_sort(windows, lambda w: (w[2], w[0]))
    last, chosen, value, examined = None, [], 0, 0
    for wid, s, f, v in order:
        examined += 1
        if last is None or s >= last:
            chosen.append(wid)
            value += v
            last = f
    return Result(value, len(chosen), chosen, _ops(c, m, examined, examined=examined))


def weighted_dp(windows):
    """Primary (value): weighted-interval DP with binary search and traceback."""
    check_windows(windows)
    order, c, m = merge_sort(windows, lambda w: (w[2], w[0]))
    n = len(order)
    finishes = [w[2] for w in order]
    best = [0] * (n + 1)
    take = [False] * (n + 1)
    pred = [0] * (n + 1)
    steps = cells = 0
    for i in range(1, n + 1):
        _, s, _, v = order[i - 1]
        p, st = _count_le(finishes, s, i - 1)      # earlier windows finishing by s
        steps += st
        cells += 1
        cand = v + best[p]
        if cand > best[i - 1]:
            best[i], take[i], pred[i] = cand, True, p
        else:
            best[i] = best[i - 1]
    chosen, i = [], n
    while i > 0:
        if take[i]:
            chosen.append(order[i - 1][0])
            i = pred[i]
        else:
            i -= 1
    chosen.reverse()
    return Result(best[n], len(chosen), chosen,
                  _ops(c, m, steps + cells, search_steps=steps, cells=cells))


def greedy_value(windows):
    """Baseline: highest value first, skip any window that overlaps a chosen one."""
    check_windows(windows)
    order, c, m = merge_sort(windows, lambda w: (-w[3], w[0]))
    sel = []                                        # (start, finish, id, value), sorted by (start, finish)
    value = examined = steps = shifts = 0
    for wid, s, f, v in order:
        examined += 1
        lo, hi = 0, len(sel)
        while lo < hi:
            steps += 1
            mid = (lo + hi) // 2
            a, b = sel[mid][0], sel[mid][1]
            if a < s or (a == s and b < f):
                lo = mid + 1
            else:
                hi = mid
        if (lo == 0 or sel[lo - 1][1] <= s) and (lo == len(sel) or f <= sel[lo][0]):
            shifts += len(sel) - lo
            sel.insert(lo, (s, f, wid, v))
            value += v
    chosen = [e[2] for e in sel]
    return Result(value, len(chosen), chosen,
                  _ops(c, m, examined + steps + shifts, examined=examined,
                       search_steps=steps, shifts=shifts))


# ---- data helpers -----------------------------------------------------------
def windows_from_df(df):
    """DataFrame of one case (columns window_id, start, finish, value) -> list of tuples."""
    d = df.sort_values("window_id")
    return [(int(a), int(b), int(c), int(e))
            for a, b, c, e in zip(d["window_id"], d["start"], d["finish"], d["value"])]


def available(windows, day):
    """Campaign rule (Section 7.4): windows whose window_id + day is divisible by 5 are unavailable."""
    if not _is_int(day) or not 1 <= day <= 7:
        raise SchedulingInputError(f"day must be 1..7, got {day!r}")
    return [w for w in windows if (w[0] + day) % 5 != 0]


def pool_windows(lists, block=1440):
    """Pooling (Section 4.3): join cases, shift case k by k*block minutes, renumber ids 1..N."""
    out, nid = [], 1
    for k, ws in enumerate(lists):
        for _, s, f, v in sorted(ws):
            out.append((nid, s + k * block, f + k * block, v))
            nid += 1
    return out