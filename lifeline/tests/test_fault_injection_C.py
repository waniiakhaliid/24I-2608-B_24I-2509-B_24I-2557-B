import random
import modules.scheduling as S
from modules.scheduling import earliest_finish, weighted_dp, SchedulingInputError
from reference import windows_bruteforce
from test_scheduling import rand_windows


def ef_count_with_bug(ws, bug):
    key = (lambda w: (w[1], w[2], w[0])) if bug == "by_start" else (lambda w: (w[2], w[1], w[0]))
    last, count = float("-inf"), 0
    for wid, s, f, v in sorted(ws, key=key):
        ok = s > last if bug == "strict" else s >= last        # fault: touching excluded
        if ok:
            count += 1
            last = f
    return count


def dp_value_with_bug(ws, bug):
    order = sorted(ws, key=lambda w: (w[2], w[1], w[0]))
    best = [0] * (len(order) + 1)
    for i, (wid, s, f, v) in enumerate(order, 1):
        if bug == "touching":                                    # fault: finish == start counted as overlap
            p = sum(1 for w in order[:i - 1] if w[2] < s)
        else:
            p = sum(1 for w in order[:i - 1] if w[2] <= s)
        best[i] = max(best[i - 1], v + best[p])
    return best[-1]


def reference_check_fails(solver, which):
    """The reference check used by the real tests: compare with brute force.
    which = 0 compares the count, 1 compares the value."""
    rng = random.Random(84)
    for _ in range(300):
        ws = rand_windows(rng)
        if solver(ws) != windows_bruteforce(ws)[which]:
            return True
    return False


def test_real_algorithms_pass_check():
    assert not reference_check_fails(lambda ws: earliest_finish(ws).count, 0)
    assert not reference_check_fails(lambda ws: weighted_dp(ws).value, 1)


def test_fault_wrong_boundary_is_caught():
    assert reference_check_fails(lambda ws: ef_count_with_bug(ws, "strict"), 0)


def test_fault_wrong_sort_key_is_caught():
    assert reference_check_fails(lambda ws: ef_count_with_bug(ws, "by_start"), 0)


def test_fault_dp_touching_off_by_one_is_caught():
    assert reference_check_fails(lambda ws: dp_value_with_bug(ws, "touching"), 1)


def test_fault_missing_validation_is_caught(monkeypatch):
    monkeypatch.setattr(S, "check_windows", lambda w: None)    # remove the validation layer
    try:
        S.earliest_finish([(1, 5, 3, 1)])                       # finish before start must be rejected
        rejected = False
    except SchedulingInputError:
        rejected = True
    assert not rejected                                         # without validation it slips through: fault detectedq