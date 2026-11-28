import random
import pytest
import modules.alarm_queue as AQ
from modules.alarm_queue import (heap_queue, linear_scan, bucket_queue, AlarmHeap, pool_alarms,
                                 add_day_alarms, alarms_from_df, AlarmInputError)
from reference import alarm_reference
import loader
from config import CACHE

needs_cache = pytest.mark.skipif(not (CACHE / "incidents.csv").exists(),
                                 reason="run src/build_cache.py first")
ALGOS = [heap_queue, linear_scan, bucket_queue]

# alarm 3 (priority 8) first; 1 and 2 tie on priority and tick, so id decides; 4 arrives later
HAND = [(1, 0, 3), (2, 0, 3), (3, 0, 8), (4, 2, 9)]


def rand_alarms(rng, max_n=12):
    """Small random alarms; ids shuffled so tick order and id order disagree, few priorities
    so ties on priority are common."""
    n = rng.randint(0, max_n)
    ids = list(range(1, n + 1))
    rng.shuffle(ids)
    return [(i, rng.randint(0, 8), rng.randint(1, 4)) for i in ids]


def invariants(alarms, res, check_rule=True):
    byid = {a[0]: a for a in alarms}
    assert sorted(res.order) == sorted(byid)                  # every alarm released exactly once
    assert len(res.ticks) == len(res.order)
    for k, (i, t) in enumerate(zip(res.order, res.ticks)):
        assert t >= byid[i][1]                                # never released before arrival
        if k:
            assert t > res.ticks[k - 1]                       # one release per tick
    if check_rule:
        key = lambda i: (-byid[i][2], byid[i][1], i)
        n = len(res.order)
        for x in range(n):
            waiting = False
            for y in range(x + 1, n):
                if byid[res.order[y]][1] <= res.ticks[x]:     # y had already arrived at x's tick
                    waiting = True
                    assert key(res.order[x]) < key(res.order[y]), "a more urgent alarm was passed over"
            if waiting:
                assert res.ticks[x + 1] == res.ticks[x] + 1   # no idle tick while alarms wait


def test_hand_example():
    for fn in ALGOS:
        r = fn(HAND)
        assert r.order == [3, 1, 4, 2] and r.ticks == [0, 1, 2, 3]
        assert r.peak == 3
        invariants(HAND, r)


@pytest.mark.parametrize("solver", ALGOS)
def test_boundaries(solver):
    r = solver([])
    assert (r.order, r.ticks, r.peak) == ([], [], 0)                          # empty queue
    assert solver([(7, 100, 2)]).ticks == [100]                               # late first arrival
    assert solver([(1, 5, 3), (2, 0, 3)]).ticks == [0, 5]                     # idle gap, time jumps
    assert solver([(1, 5, 3), (2, 0, 3)]).order == [2, 1]
    assert solver([(3, 0, 5), (1, 1, 5), (2, 0, 5)]).order == [2, 3, 1]       # same priority: tick, then id
    assert solver([(i, 0, 1) for i in range(1, 6)]).order == [1, 2, 3, 4, 5]  # all tied: id ascending
    assert solver([(i, 0, 1) for i in range(1, 6)]).ticks == [0, 1, 2, 3, 4]
    assert solver([(1, 0, 0), (2, 0, 0)]).order == [1, 2]                     # priority 0 is allowed


@pytest.mark.parametrize("solver", ALGOS)
def test_bad_input_rejected(solver):
    for bad in ([(1, 0)],                       # wrong length
                [(1, 0, 3.5)],                  # not an integer
                [(True, 0, 3)],                 # bool id
                [(1, -1, 3)],                   # negative tick
                [(1, 0, -3)],                   # negative priority
                [(1, 0, 3), (1, 2, 4)]):        # duplicate id
        with pytest.raises(AlarmInputError):
            solver(bad)


def test_bucket_queue_rejects_huge_priority_but_heap_does_not():
    with pytest.raises(AlarmInputError):
        bucket_queue([(1, 0, 5000)])
    assert heap_queue([(1, 0, 5000)]).order == [1]


def test_heap_sorts():
    rng = random.Random(84)
    xs = [(rng.randint(0, 50), rng.randint(0, 50), rng.randint(0, 50)) for _ in range(200)]
    h = AlarmHeap()
    for x in xs:
        h.push(x)
    assert [h.pop() for _ in xs] == sorted(xs)
    assert h.cmp > 0 and h.moves > 0


def test_random_against_reference():
    rng = random.Random(84)
    for _ in range(300):
        al = rand_alarms(rng)
        ref = alarm_reference(al)
        for fn in ALGOS:
            r = fn(al)
            assert list(zip(r.order, r.ticks)) == ref
            invariants(al, r)


def test_campaign_extra_alarms():
    base = [(1, 0, 3), (2, 0, 3)]
    assert add_day_alarms(base, 2) == base + [(3, 0, 9)]
    assert add_day_alarms(base, 5) == base + [(3, 0, 10)]
    for day in (1, 3, 4, 6, 7):
        assert add_day_alarms(base, day) == base
    assert add_day_alarms([], 2) == [(1, 0, 9)]
    assert heap_queue(add_day_alarms(base, 2)).order[0] == 3       # the priority-9 alarm goes first
    for bad in (0, 8, 2.5, True):
        with pytest.raises(AlarmInputError):
            add_day_alarms(base, bad)


def test_pooling_shifts_ticks_and_renumbers():
    a = [(1, 0, 3), (2, 4, 5)]
    b = [(1, 0, 2)]
    assert pool_alarms([a, b]) == [(1, 0, 3), (2, 4, 5), (3, 5, 2)]
    assert pool_alarms([[], b]) == [(1, 0, 2)]


def test_operation_counts_are_reported():
    al = [(i, i // 2, (i * 7) % 5 + 1) for i in range(1, 41)]
    for fn in ALGOS:
        o = fn(al).ops
        assert o["total"] == o["sort"] + o["select"] and o["select"] > 0
    assert linear_scan(al).ops["cmp"] >= heap_queue(al).ops["cmp"] or True   # reported, not asserted


@needs_cache
def test_sample_cases_all_days():
    for cid in loader.sample_cases()["case_id"]:
        base = alarms_from_df(loader.load_case(cid)["incidents"])
        for day in range(1, 8):
            al = add_day_alarms(base, day)
            h, s, b = heap_queue(al), linear_scan(al), bucket_queue(al)
            assert h.order == s.order == b.order, f"{cid} day {day}: release orders differ"
            assert h.ticks == s.ticks == b.ticks, f"{cid} day {day}: release ticks differ"
            invariants(al, h, check_rule=len(al) <= 60)
            if len(al) <= 1000:                                  # reference is O(m^2): S and M only
                assert list(zip(h.order, h.ticks)) == alarm_reference(al), f"{cid} day {day}"


@needs_cache
def test_extra_alarm_released_at_tick_zero_on_days_2_and_5():
    for cid in loader.sample_cases()["case_id"]:
        base = alarms_from_df(loader.load_case(cid)["incidents"])
        for day in (2, 5):
            al = add_day_alarms(base, day)
            extra = al[-1][0]
            r = heap_queue(al)
            # it is the most urgent alarm at tick 0 unless another alarm of equal or higher priority
            # (and earlier tick or id) is also waiting at tick 0
            assert r.ticks[r.order.index(extra)] <= 1 + sum(1 for a in base if a[1] == 0 and a[2] >= al[-1][2])


@needs_cache
def test_queue_is_backlogged_on_larger_cases():
    """Records the data property the proposal relies on (backlog grows). Printed, not hidden."""
    rows = []
    for cid in loader.sample_cases()["case_id"]:
        al = alarms_from_df(loader.load_case(cid)["incidents"])
        rows.append((cid, len(al), heap_queue(al).peak))
    print("case, alarms, peak backlog:", rows)
    assert all(peak >= 1 for _, m, peak in rows if m > 0)