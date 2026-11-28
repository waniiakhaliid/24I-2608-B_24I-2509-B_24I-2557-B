import random
import pytest
import modules.scheduling as S
from modules.scheduling import (earliest_finish, weighted_dp, greedy_value, merge_sort,
                                pool_windows, available, windows_from_df, SchedulingInputError)
from reference import windows_bruteforce
import loader
from config import CACHE

needs_cache = pytest.mark.skipif(not (CACHE / "windows.csv").exists(),
                                 reason="run src/build_cache.py first")
ALGOS = [earliest_finish, weighted_dp, greedy_value]

# hand example: EF picks 1,2 (count 2); DP picks 1,2 (value 10); value-greedy picks 3 (value 8)
HAND = [(1, 0, 10, 5), (2, 10, 20, 5), (3, 0, 20, 8), (4, 5, 15, 7)]


def rand_windows(rng, max_n=10):
    """Small random windows; times 0..12 so touching windows are common."""
    out = []
    for i in range(rng.randint(0, max_n)):
        s = rng.randint(0, 12)
        out.append((i + 1, s, s + rng.randint(1, 6), rng.randint(0, 20)))
    return out


def invariants(res, windows):
    byid = {w[0]: w for w in windows}
    assert len(set(res.chosen)) == len(res.chosen)              # no window twice
    sel = [byid[i] for i in res.chosen]                          # every chosen window exists
    for a, b in zip(sel, sel[1:]):
        assert a[2] <= b[1], f"windows {a[0]} and {b[0]} overlap"   # compatible, in time order
    assert res.count == len(sel)
    assert res.value == sum(w[3] for w in sel)


def test_hand_example():
    ef, dp, vg = earliest_finish(HAND), weighted_dp(HAND), greedy_value(HAND)
    assert (ef.count, ef.chosen) == (2, [1, 2])
    assert (dp.value, dp.chosen) == (10, [1, 2])
    assert (vg.value, vg.chosen) == (8, [3])
    for r in (ef, dp, vg):
        invariants(r, HAND)


@pytest.mark.parametrize("solver", ALGOS)
def test_boundaries(solver):
    r = solver([])
    assert (r.value, r.count, r.chosen) == (0, 0, [])                       # no windows
    assert solver([(1, 0, 5, 3)]).count == 1                                 # single window
    assert solver([(1, 0, 10, 4), (2, 10, 20, 4)]).count == 2                # touching: compatible
    assert solver([(1, 0, 5, 3), (2, 0, 5, 3)]).count == 1                   # identical windows
    assert solver([(1, 0, 9, 3), (2, 1, 8, 3), (3, 2, 7, 3)]).count == 1     # all overlap


@pytest.mark.parametrize("solver", ALGOS)
def test_bad_input_rejected(solver):
    for bad in ([(1, 5, 3, 1)],                    # finish before start
                [(1, 0, 5, -1)],                   # negative value
                [(1, 0, 5, 1), (1, 6, 7, 1)],      # duplicate id
                [(1, 0, 5)],                       # wrong length
                [(1, 0.5, 5, 1)],                  # not an integer
                [(True, 0, 5, 1)],                 # bool id
                [(1, -1, 5, 1)]):                  # negative start
        with pytest.raises(SchedulingInputError):
            solver(bad)


def test_merge_sort_matches_sorted_and_is_stable():
    rng = random.Random(84)
    for _ in range(100):
        xs = [(rng.randint(0, 5), i) for i in range(rng.randint(0, 40))]
        out, _, _ = merge_sort(xs, key=lambda x: x[0])
        assert out == sorted(xs, key=lambda x: x[0])           # sorted() is stable too


def test_random_against_bruteforce():
    rng = random.Random(84)
    for _ in range(300):
        ws = rand_windows(rng)
        bc, bv = windows_bruteforce(ws)
        ef, dp, vg = earliest_finish(ws), weighted_dp(ws), greedy_value(ws)
        assert ef.count == bc
        assert dp.value == bv
        for r in (ef, dp, vg):
            invariants(r, ws)
        assert vg.value <= dp.value and ef.value <= dp.value
        assert vg.count <= ef.count and dp.count <= ef.count


def test_campaign_availability_rule():
    ws = [(i, 0, 5, 1) for i in range(1, 11)]
    assert [w[0] for w in available(ws, 1)] == [1, 2, 3, 5, 6, 7, 8, 10]     # 4 and 9 removed
    assert [w[0] for w in available(ws, 5)] == [1, 2, 3, 4, 6, 7, 8, 9]      # 5 and 10 removed
    with pytest.raises(SchedulingInputError):
        available(ws, 0)
    with pytest.raises(SchedulingInputError):
        available(ws, 8)
    assert weighted_dp(available([(5, 0, 5, 9)], 5)).value == 0              # everything unavailable


def test_pooling_shifts_and_renumbers():
    a = [(1, 0, 10, 5), (2, 10, 20, 5)]
    b = [(1, 0, 5, 3)]
    p = pool_windows([a, b])
    assert p == [(1, 0, 10, 5), (2, 10, 20, 5), (3, 1440, 1445, 3)]
    assert earliest_finish(p).count == 3


def _case_windows(cid):
    c = loader.load_case(cid)
    return c, windows_from_df(c["windows"])


@needs_cache
def test_tier_s_against_claims():
    s = loader.sample_cases()
    for cid in s[s.tier == "S"]["case_id"]:
        c, ws = _case_windows(cid)
        claim_count = int(c["claims"]["window_count_opt"].iloc[0])
        claim_value = int(c["claims"]["window_value_opt"].iloc[0])
        ef, dp = earliest_finish(ws), weighted_dp(ws)
        invariants(ef, ws)
        invariants(dp, ws)
        assert ef.count == claim_count, f"{cid}: EF count {ef.count} != claim {claim_count}"
        assert dp.value == claim_value, f"{cid}: DP value {dp.value} != claim {claim_value}"


@needs_cache
def test_sample_cases_all_days_invariants():
    for cid in loader.sample_cases()["case_id"]:
        _, base = _case_windows(cid)
        for day in range(1, 8):
            ws = available(base, day)
            ef, dp, vg = earliest_finish(ws), weighted_dp(ws), greedy_value(ws)
            for r in (ef, dp, vg):
                invariants(r, ws)
            assert dp.value >= vg.value and dp.value >= ef.value, f"{cid} day {day}"
            assert ef.count >= vg.count and ef.count >= dp.count, f"{cid} day {day}"


@needs_cache
def test_pooled_equals_sum_of_cases():
    """Pooled blocks are independent, so optima add up. If this fails, some case has windows
    past minute 1440: report it, do not hide it."""
    ids = list(loader.sample_cases()["case_id"])[:4]
    lists = [_case_windows(i)[1] for i in ids]
    pooled = pool_windows(lists)
    assert earliest_finish(pooled).count == sum(earliest_finish(w).count for w in lists)
    assert weighted_dp(pooled).value == sum(weighted_dp(w).value for w in lists)


@needs_cache
def test_value_greedy_loses_somewhere():
    """If this fails, greedy by value is never worse on the sample: report it, do not hide it."""
    losses = []
    for cid in loader.sample_cases()["case_id"]:
        _, ws = _case_windows(cid)
        d, g = weighted_dp(ws).value, greedy_value(ws).value
        if g < d:
            losses.append((cid, g, d, round(g / d, 3)))
    print("value-greedy below DP on:", losses)
    assert losses