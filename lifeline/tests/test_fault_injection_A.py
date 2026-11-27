import random
import modules.knapsack as K
from modules.knapsack import knapsack_dp
from reference import knapsack_bruteforce


def dp_value_with_bug(weights, values, cap, bug):
    n = len(weights) - (1 if bug == "loop_bound" else 0)     # fault 3: skips last crate
    best = [0] * (cap + 1)
    for i in range(n):
        wi, vi = weights[i], values[i]
        if bug == "boundary":                                 # fault 1: misses w == wi
            rng = range(cap, wi, -1)
        elif bug == "direction":                              # fault 2: crate reused
            rng = range(wi, cap + 1)
        else:
            rng = range(cap, wi - 1, -1)
        for w in rng:
            best[w] = max(best[w], best[w - wi] + vi)
    return best[cap]


def reference_check_fails(solver_value):
    """The reference check used by the real tests: compare with brute force."""
    rng = random.Random(84)
    for _ in range(300):
        n = rng.randint(1, 10)
        w = [rng.randint(1, 20) for _ in range(n)]
        v = [rng.randint(1, 100) for _ in range(n)]
        cap = rng.randint(1, sum(w))
        if solver_value(w, v, cap) != knapsack_bruteforce(w, v, cap)[0]:
            return True
    return False


def test_real_dp_passes_check():
    assert not reference_check_fails(lambda w, v, c: knapsack_dp(w, v, c).value)


def test_fault_wrong_boundary_is_caught():
    assert reference_check_fails(lambda w, v, c: dp_value_with_bug(w, v, c, "boundary"))


def test_fault_wrong_loop_direction_is_caught():
    assert reference_check_fails(lambda w, v, c: dp_value_with_bug(w, v, c, "direction"))


def test_fault_off_by_one_loop_bound_is_caught():
    assert reference_check_fails(lambda w, v, c: dp_value_with_bug(w, v, c, "loop_bound"))


def test_fault_missing_validation_is_caught(monkeypatch):
    monkeypatch.setattr(K, "check_input", lambda *a: None)   # remove the validation layer
    try:
        K.knapsack_dp([0], [1], 5)       # weight 0 should be rejected
        rejected = False
    except K.KnapsackInputError:
        rejected = True
    assert not rejected                  # without validation the bad input slips through: fault detected