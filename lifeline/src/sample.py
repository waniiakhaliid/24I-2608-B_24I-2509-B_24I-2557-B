"""Pick the group sample from master_release_v1.

Rule (project notes): per tier, take rows at positions s mod 7,
s mod 7 + 7, ... in master order, then keep the first N.
Seed s = 84, so the start position is 0.
N per tier is our own choice (the statement does not fix it).
"""
from pathlib import Path
import pandas as pd

SEED = 84
N = {"S": 10, "M": 5, "L": 3, "X": 4}
TRAP_CASE_NOS = {46, 47, 48, 49}

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "cases.csv"
OUT = ROOT / "results" / "sample_cases.csv"


def pick_sample(cases: pd.DataFrame, seed: int = SEED, n_per_tier: dict = N) -> pd.DataFrame:
    start = seed % 7
    parts = []
    for tier, n in n_per_tier.items():
        t = cases[cases["tier"] == tier].reset_index(drop=True)  # keeps file order
        parts.append(t.iloc[start::7].head(n))
    return pd.concat(parts, ignore_index=True)


def main():
    cases = pd.read_csv(CASES)
    print("columns:", list(cases.columns))
    print(cases["tier"].value_counts().to_string(), "\n")

    sample = pick_sample(cases)

    # Requirements: >= 5 cases, one tier L, one trap case (46..49)
    has_l = (sample["tier"] == "L").any()
    traps = sample[sample["case_no"].isin(TRAP_CASE_NOS)]
    print(f"cases: {len(sample)} | tier L present: {has_l} | trap cases: {len(traps)}")
    if len(sample) < 5 or not has_l or traps.empty:
        print("WARNING: sample misses a requirement; add cases explicitly and document it.")

    cols = ["case_id", "group_no", "case_no", "tier", "scenario", "capacity"]
    print(sample[cols].to_string(index=False))

    OUT.parent.mkdir(exist_ok=True)
    sample.to_csv(OUT, index=False)
    print(f"\nsaved {OUT}")


if __name__ == "__main__":
    main()