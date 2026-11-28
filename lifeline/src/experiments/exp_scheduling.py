"""Module C experiments: scaling on pooled windows, quality per case, and the 7 campaign days."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # makes src/ importable

import math
import tracemalloc
import pandas as pd
import loader
from config import CACHE, RESULTS
from harness import time_it, log_row, reset_module
from stats import loglog_fit
from modules.scheduling import (earliest_finish, weighted_dp, greedy_value, pool_windows,
                                windows_from_df, available)

SIZES = [200, 400, 800, 1600, 3200]
ALGOS = {"EF-greedy": earliest_finish, "Weighted-DP": weighted_dp, "Value-greedy": greedy_value}


def case_lists():
    wi = pd.read_csv(CACHE / "windows.csv")
    ids = list(loader.sample_cases()["case_id"])
    return ids, [windows_from_df(wi[wi.case_id == cid]) for cid in ids]


def note_of(res):
    return f"count={res.count};value={res.value};" + ";".join(f"{k}={v}" for k, v in res.ops.items())


def scaling(lists):
    pooled_all = pool_windows(lists)
    data = {k: [] for k in ALGOS}
    results = {k: {} for k in ALGOS}
    for n in SIZES:
        ws = pooled_all[:n]
        for name, fn in ALGOS.items():
            med, iqr, res = time_it(fn, ws)
            tracemalloc.start()
            fn(ws)
            mem = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
            if med is None:
                log_row(module="C", experiment="scaling", algorithm=name, instance=f"pool{n}",
                        size=len(ws), status="DNF")
                continue
            log_row(module="C", experiment="scaling", algorithm=name, instance=f"pool{n}",
                    size=len(ws), time_s=med, time_iqr_s=iqr, ops=res.ops["total"],
                    mem_bytes=mem, status="OK", note=note_of(res))
            data[name].append((n, med))
            results[name][n] = res
            print(f"{name:12s} n={n:5d} time={med:.5f}s ops={res.ops['total']} "
                  f"count={res.count} value={res.value}")
        if all(n in results[k] for k in ALGOS):
            assert results["Weighted-DP"][n].value >= results["Value-greedy"][n].value
            assert results["EF-greedy"][n].count >= results["Value-greedy"][n].count
    lines = []
    for name, pts in data.items():
        if len(pts) < 5:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        slope, ci, r2, _ = loglog_fit(xs, ys)
        a, _, _, b = loglog_fit(xs[:4], ys[:4])
        err = abs(math.exp(b + a * math.log(xs[-1])) - ys[-1]) / ys[-1]
        lines.append(f"{name}: slope={slope:.3f} +/- {ci:.3f} (95% CI) R2={r2:.4f} "
                     f"prediction error at n={xs[-1]}: {err:.1%}")
    last = SIZES[-1]
    if all(last in results[k] for k in ALGOS):
        t = {k: data[k][-1][1] for k in ALGOS}
        lines.append(f"Weighted-DP / EF-greedy time at n={last}: {t['Weighted-DP'] / t['EF-greedy']:.2f}")
    if all(len(results[k]) == len(SIZES) for k in ALGOS):
        lines.append("Value-greedy value / DP value: " + ", ".join(
            f"n={n}: {results['Value-greedy'][n].value / results['Weighted-DP'][n].value:.3f}" for n in SIZES))
        lines.append("Value-greedy count / EF count: " + ", ".join(
            f"n={n}: {results['Value-greedy'][n].count / results['EF-greedy'][n].count:.3f}" for n in SIZES))
    (RESULTS / "fit_C.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))


def quality(ids, lists):
    """Every sample case, all windows, one run per algorithm (no timing)."""
    for cid, ws in zip(ids, lists):
        for name, fn in ALGOS.items():
            res = fn(ws)
            log_row(module="C", experiment="quality", algorithm=name, instance=cid,
                    size=len(ws), ops=res.ops["total"], status="OK", note=note_of(res))
        print(cid, "quality done")


def days(ids, lists):
    """Every sample case on every campaign day, with the day's unavailable windows removed."""
    for cid, base in zip(ids, lists):
        for day in range(1, 8):
            ws = available(base, day)
            for name, fn in ALGOS.items():
                res = fn(ws)
                log_row(module="C", experiment="days", algorithm=name, instance=cid,
                        size=len(ws), size2=day, ops=res.ops["total"], status="OK",
                        note=f"day={day};count={res.count};value={res.value}")
        print(cid, "days done")


if __name__ == "__main__":
    reset_module("C")
    ids, lists = case_lists()
    scaling(lists)
    quality(ids, lists)
    days(ids, lists)