import random
import pytest
from modules.knapsack import (knapsack_dp, knapsack_greedy,
                              crate_arrays, KnapsackInputError)
from reference import knapsack_bruteforce
import loader
from config import CACHE

needs_cache = pytest.mark.skipif(not (CACHE / "crates.csv").exists(),
                                 reason="run src/build_cache.py first")
SOLVERS = [knapsack_dp, knapsack_greedy]


def invariants(res, w, v, cap):
    assert sum(w[i] for i in res.chosen) <= cap          # load within capacity
    assert len(set(res.chosen)) == len(res.chosen)       # no crate twice
    assert res.weight == sum(w[i] for i in res.chosen)
    assert res.value == sum(v[i] for i in res.chosen)


def test_hand_example():
    w, v = [1, 3, 4, 5], [1, 4, 5, 7]
    r = knapsack_dp(w, v, 7)
    assert r.value == 9 and r.chosen == [1, 2]


@pytest.mark.parametrize("solver", SOLVERS)
def test_boundaries(solver):
    assert solver([], [], 10).value == 0                 # no crates
    assert solver([3, 4], [5, 6], 0).value == 0          # capacity 0
    assert solver([30, 40], [5, 6], 10).chosen == []     # truck too small
    assert solver([10], [7], 10).value == 7              # exact fit


@pytest.mark.parametrize("solver", SOLVERS)
def test_bad_input_rejected(solver):
    for args in [([1], [1, 2], 5), ([1], [1], -1), ([0], [1], 5),
                 ([-2], [1], 5), ([1], [-1], 5), ([1.5], [1], 5)]:
        with pytest.raises(KnapsackInputError):
            solver(*args)


def test_dp_matches_bruteforce_random():
    rng = random.Random(84)
    for _ in range(300):
        n = rng.randint(0, 12)
        w = [rng.randint(1, 20) for _ in range(n)]
        v = [rng.randint(0, 100) for _ in range(n)]
        cap = rng.randint(0, max(1, sum(w)))
        d, g = knapsack_dp(w, v, cap), knapsack_greedy(w, v, cap)
        b = knapsack_bruteforce(w, v, cap)[0]
        assert d.value == b
        invariants(d, w, v, cap)
        invariants(g, w, v, cap)
        assert g.value <= d.value


def _case(case_id):
    c = loader.load_case(case_id)
    w, v = crate_arrays(c["crates"])
    return c, w, v, int(c["meta"]["capacity"])


@needs_cache
def test_tier_s_against_claims():
    s = loader.sample_cases()
    for cid in s[s.tier == "S"]["case_id"]:
        c, w, v, cap = _case(cid)
        claim = int(c["claims"]["cargo_opt"].iloc[0])
        r = knapsack_dp(w, v, cap)
        invariants(r, w, v, cap)
        assert r.value == claim, f"{cid}: DP {r.value} != claim {claim}"
        assert knapsack_bruteforce(w, v, cap)[0] == claim


@needs_cache
def test_invariants_on_medium_cases():
    s = loader.sample_cases()
    for cid in s[s.tier == "M"]["case_id"]:
        _, w, v, cap = _case(cid)
        d, g = knapsack_dp(w, v, cap), knapsack_greedy(w, v, cap)
        invariants(d, w, v, cap)
        invariants(g, w, v, cap)
        assert g.value <= d.value


@needs_cache
def test_trap_47_greedy_loses():
    """If this fails, group 7's trap does not fool ratio greedy: report it, do not hide it."""
    _, w, v, cap = _case("7-47")
    d, g = knapsack_dp(w, v, cap), knapsack_greedy(w, v, cap)
    print(f"trap 7-47: greedy {g.value} / dp {d.value} = {g.value / d.value:.2f}")
    assert g.value < d.value


def test_campaign_multipliers():
    import pandas as pd
    df = pd.DataFrame({"crate_id": [1, 2, 3], "cat": [0, 2, 3],
                       "weight": [1, 1, 1], "value": [10, 10, 10]})
    _, v = crate_arrays(df, {0: 2, 2: 3})
    assert v == [20, 30, 10]