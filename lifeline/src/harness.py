"""Timing per the statement: 1 warm-up, median of 5, IQR, single thread.
Results go to results/results_<module>.csv; combine() builds results.csv."""
import csv
import statistics
import time

import pandas as pd

from config import RESULTS, RESULTS_CSV

COLUMNS = ["module", "experiment", "algorithm", "instance", "size", "size2",
           "time_s", "time_iqr_s", "ops", "mem_bytes", "status", "note"]
TIMEOUT_S = 300


def time_it(fn, *args, runs=5):
    fn(*args)                                   # warm-up, discarded
    times, result = [], None
    for _ in range(runs):
        t0 = time.perf_counter()
        result = fn(*args)
        times.append(time.perf_counter() - t0)
        if times[-1] > TIMEOUT_S:
            return None, None, result           # caller records DNF
    q = statistics.quantiles(times, n=4)
    return statistics.median(times), q[2] - q[0], result


def module_csv(module):
    return RESULTS / f"results_{module}.csv"


def reset_module(module):
    """Call at the start of a module's experiment script: a rerun replaces, not appends."""
    module_csv(module).unlink(missing_ok=True)


def log_row(**row):
    path = module_csv(row["module"])
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        w.writerow({c: row.get(c, "") for c in COLUMNS})


def combine():
    """Merge all results_<module>.csv into the required results.csv."""
    parts = [pd.read_csv(p) for p in sorted(RESULTS.glob("results_*.csv"))]
    if not parts:
        print("no results_<module>.csv files found")
        return
    pd.concat(parts, ignore_index=True)[COLUMNS].to_csv(RESULTS_CSV, index=False)
    print(f"combined {len(parts)} files into {RESULTS_CSV}")