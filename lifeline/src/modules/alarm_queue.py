"""Module D: emergency queue. Written from scratch (own binary heap; arrivals sorted with the
project's own merge sort from modules.scheduling).

An alarm is a tuple (alarm_id, tick, priority).

Release rule: one alarm per tick, chosen among the alarms that have arrived (tick <= now).
If nothing is waiting, time jumps to the next arrival tick.
Urgency order (Section 4.4): priority descending, then tick ascending, then alarm_id ascending.

Operation counts (defined in README); preprocessing (the arrival sort) is counted separately:
  sort   : key comparisons + element placements of the merge sort
  heap   : key comparisons + element moves (a swap counts as 2)
  scan   : key comparisons + element shifts when an item leaves the pending list
  bucket : appends + pops + level checks
  total  = sort + select
"""
from typing import NamedTuple

from modules.scheduling import merge_sort

MAX_LEVELS = 1000


class AlarmInputError(ValueError):
    pass


class Result(NamedTuple):
    order: list      # alarm_ids in release order
    ticks: list      # release tick of each alarm, same order
    peak: int        # largest number of alarms waiting at once
    ops: dict


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def check_alarms(alarms):
    seen = set()
    for a in alarms:
        if not isinstance(a, (tuple, list)) or len(a) != 3:
            raise AlarmInputError(f"alarm must be (alarm_id, tick, priority), got {a!r}")
        aid, tick, pr = a
        if not all(_is_int(x) for x in a):
            raise AlarmInputError(f"alarm fields must be integers, got {a!r}")
        if tick < 0:
            raise AlarmInputError(f"alarm {aid}: negative tick {tick}")
        if pr < 0:
            raise AlarmInputError(f"alarm {aid}: negative priority {pr}")
        if aid in seen:
            raise AlarmInputError(f"duplicate alarm_id {aid}")
        seen.add(aid)


class AlarmHeap:
    """Binary min-heap with operation counts."""

    def __init__(self):
        self.a = []
        self.cmp = 0
        self.moves = 0

    def __len__(self):
        return len(self.a)

    def push(self, item):
        a = self.a
        a.append(item)
        self.moves += 1
        i = len(a) - 1
        while i > 0:
            p = (i - 1) // 2
            self.cmp += 1
            if a[i] < a[p]:
                a[i], a[p] = a[p], a[i]
                self.moves += 2
                i = p
            else:
                break

    def pop(self):
        a = self.a
        top, last = a[0], a.pop()
        if a:
            a[0] = last
            self.moves += 1
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
                self.moves += 2
                i = m
        return top


def _simulate(arrivals, add, pop, size):
    """Shared release loop. arrivals sorted by (tick, alarm_id); add(alarm), pop() -> alarm_id."""
    n, i, t, peak = len(arrivals), 0, 0, 0
    ids, ticks = [], []
    while i < n or size() > 0:
        if size() == 0 and arrivals[i][1] > t:
            t = arrivals[i][1]                       # idle: jump to the next arrival
        while i < n and arrivals[i][1] <= t:
            add(arrivals[i])
            i += 1
        if size() > peak:
            peak = size()
        ids.append(pop())
        ticks.append(t)
        t += 1
    return ids, ticks, peak


def _prepare(alarms):
    check_alarms(alarms)
    return merge_sort(alarms, lambda a: (a[1], a[0]))


def _ops(sort_cmp, sort_moves, select, **extra):
    d = {"total": sort_cmp + sort_moves + select, "sort": sort_cmp + sort_moves,
         "select": select}
    d.update(extra)
    return d


def heap_queue(alarms):
    """Primary: binary heap on (-priority, tick, alarm_id)."""
    arrivals, c, m = _prepare(alarms)
    heap = AlarmHeap()
    ids, ticks, peak = _simulate(
        arrivals,
        lambda a: heap.push((-a[2], a[1], a[0])),
        lambda: heap.pop()[2],
        lambda: len(heap))
    return Result(ids, ticks, peak,
                  _ops(c, m, heap.cmp + heap.moves, cmp=heap.cmp, moves=heap.moves))


def linear_scan(alarms):
    """Baseline: scan the whole pending list for the most urgent alarm at every release."""
    arrivals, c, m = _prepare(alarms)
    pending = []
    cnt = {"cmp": 0, "shifts": 0}

    def pop():
        best, bk = 0, pending[0]
        for j in range(1, len(pending)):
            cnt["cmp"] += 1
            if pending[j] < bk:
                best, bk = j, pending[j]
        cnt["shifts"] += len(pending) - 1 - best
        return pending.pop(best)[2]

    ids, ticks, peak = _simulate(
        arrivals,
        lambda a: pending.append((-a[2], a[1], a[0])),
        pop,
        lambda: len(pending))
    return Result(ids, ticks, peak,
                  _ops(c, m, cnt["cmp"] + cnt["shifts"], cmp=cnt["cmp"], shifts=cnt["shifts"]))


def bucket_queue(alarms, max_levels=MAX_LEVELS):
    """Extra comparison: one FIFO list per priority level, highest non-empty level first."""
    arrivals, c, m = _prepare(alarms)
    top = max((a[2] for a in arrivals), default=0)
    if top >= max_levels:
        raise AlarmInputError(f"bucket queue needs few priority levels, got priority {top}")
    buckets = [[] for _ in range(top + 1)]
    heads = [0] * (top + 1)
    cnt = {"appends": 0, "pops": 0, "levels": 0, "size": 0}

    def add(a):
        buckets[a[2]].append(a[0])
        cnt["appends"] += 1
        cnt["size"] += 1

    def pop():
        for p in range(top, -1, -1):
            cnt["levels"] += 1
            if heads[p] < len(buckets[p]):
                aid = buckets[p][heads[p]]
                heads[p] += 1
                cnt["pops"] += 1
                cnt["size"] -= 1
                return aid

    ids, ticks, peak = _simulate(arrivals, add, pop, lambda: cnt["size"])
    return Result(ids, ticks, peak,
                  _ops(c, m, cnt["appends"] + cnt["pops"] + cnt["levels"],
                       appends=cnt["appends"], pops=cnt["pops"], level_checks=cnt["levels"]))


# ---- data and calendar helpers ---------------------------------------------------
def alarms_from_df(df):
    """DataFrame of one case (columns alarm_id, tick, priority) -> list of tuples."""
    d = df.sort_values("alarm_id")
    return [(int(a), int(t), int(p)) for a, t, p in zip(d["alarm_id"], d["tick"], d["priority"])]


def add_day_alarms(alarms, day):
    """Campaign events (Section 7.4): day 2 adds one alarm of priority 9 at tick 0,
    day 5 adds one of priority 10 at tick 0. The new alarm_id is max id + 1."""
    if not _is_int(day) or not 1 <= day <= 7:
        raise AlarmInputError(f"day must be 1..7, got {day!r}")
    extra = {2: 9, 5: 10}.get(day)
    if extra is None:
        return list(alarms)
    new_id = max((a[0] for a in alarms), default=0) + 1
    return list(alarms) + [(new_id, 0, extra)]


def pool_alarms(lists):
    """Pooling (Section 4.3): join cases, shift the ticks of each case past the previous one
    (offset += previous max tick + 1), renumber ids 1..N."""
    out, nid, offset = [], 1, 0
    for ws in lists:
        ws = sorted(ws)
        for _, t, p in ws:
            out.append((nid, t + offset, p))
            nid += 1
        if ws:
            offset += max(t for _, t, _ in ws) + 1
    return out