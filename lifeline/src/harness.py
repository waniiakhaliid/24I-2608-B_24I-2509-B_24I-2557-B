"""Timing per the statement: 1 warm-up, median of 5, IQR, single thread."""
import csv, statistics, time
from config import RESULTS_CSV

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

def log_row(**row):
    new = not RESULTS_CSV.exists()
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        w.writerow({c: row.get(c, "") for c in COLUMNS})