import random
import modules.alarm_queue as AQ
from modules.alarm_queue import heap_queue, AlarmInputError
from reference import alarm_reference
from test_alarm_queue import rand_alarms


def sim_with_bug(alarms, bug):
    """A deliberately broken copy of the release rule (plain loop, no heap)."""
    left, t, out = list(alarms), 0, []
    while left:
        horizon = t + 1 if bug == "early" else t               # fault: releases alarms that have not arrived
        ready = [a for a in left if a[1] <= horizon]
        if not ready:
            t = min(a[1] for a in left)
            continue
        if bug == "tie_tick":                                  # fault: tick ignored in the tie rule
            key = lambda a: (-a[2], a[0])
        elif bug == "ascending":                               # fault: low priority first
            key = lambda a: (a[2], a[1], a[0])
        else:
            key = lambda a: (-a[2], a[1], a[0])
        best = min(ready, key=key)
        left.remove(best)
        out.append(best[0])
        t += 1
    return out


def reference_check_fails(solver):
    """The reference check used by the real tests: compare the release order with the reference."""
    rng = random.Random(84)
    for _ in range(300):
        al = rand_alarms(rng)
        if solver(al) != [i for i, _ in alarm_reference(al)]:
            return True
    return False


def test_real_heap_passes_check():
    assert not reference_check_fails(lambda al: heap_queue(al).order)


def test_fault_wrong_tie_rule_is_caught():
    assert reference_check_fails(lambda al: sim_with_bug(al, "tie_tick"))


def test_fault_wrong_priority_direction_is_caught():
    assert reference_check_fails(lambda al: sim_with_bug(al, "ascending"))


def test_fault_release_before_arrival_is_caught():
    assert reference_check_fails(lambda al: sim_with_bug(al, "early"))


def test_fault_missing_validation_is_caught(monkeypatch):
    monkeypatch.setattr(AQ, "check_alarms", lambda a: None)     # remove the validation layer
    try:
        AQ.heap_queue([(1, -5, 3)])                             # negative tick must be rejected
        rejected = False
    except AlarmInputError:
        rejected = True
    assert not rejected                                         # without validation it slips through: fault detected