"""Shared constants: alphabet, tier ranges, deterministic RNG streams."""
import random

ALPHABET = [chr(c) for c in range(65, 91)] + [str(d) for d in range(10)] + ["_", "-"]  # 38 symbols
PATTERN_LENGTHS = (2, 4, 8, 12, 20, 40)

RANGES = {
    "S": dict(crates=(8, 20), V=(6, 12), log=(200, 500), report=(10, 30), windows=(8, 20),
              alarms=(10, 40), sites=(5, 9), stages=(4, 8), drum=(5, 14), sensors=(6, 14),
              switches=(6, 15), rations=(8, 20)),
    "M": dict(crates=(40, 200), V=(30, 150), log=(2000, 10000), report=(30, 150), windows=(50, 300),
              alarms=(200, 1000), sites=(10, 16), stages=(15, 60), drum=(40, 200), sensors=(20, 40),
              switches=(20, 50), rations=(24, 40)),
    "L": dict(crates=(500, 1500), V=(500, 2000), log=(20000, 100000), report=(200, 1000),
              windows=(1000, 3000), alarms=(2000, 5000), sites=(200, 500), stages=(100, 300),
              drum=(500, 2000), sensors=(100, 400), switches=(20, 50), rations=(50, 100)),
}
RANGES["X"] = RANGES["L"]  # trap cases use tier-L ranges unless the trap says otherwise


def tier_of(k):
    return "S" if k < 20 else "M" if k < 40 else "L" if k < 46 else "X"


def scenario_of(k):
    return k % 6 + 1


def case_id(seed, k):
    return f"{seed}-{k:02d}"


def rng_for(seed, k, name):
    """Independent deterministic stream per (group seed, case, module)."""
    return random.Random(f"lifeline|{seed}|{k}|{name}")


def ceil_pct(n, pct):
    """ceil(n * pct / 100) in integer arithmetic."""
    return -(-n * pct // 100)
