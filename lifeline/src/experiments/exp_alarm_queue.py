"""Module D experiments: scaling on pooled alarms, quality per sample case, and the 7 campaign days."""
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
from modules.alarm_queue import (heap_queue, linear_scan, bucket_queue, pool_alarms,
                                 alarms_from_df, add_day_alarms)

SIZES = [500, 1000, 2000, 4000, 8000]
ALGOS = {"Binary-heap": heap_queue, "Linear-scan": linear_scan, "Bucket-queue": bucket_queue}


def case_lists():
    inc = pd.read_csv(CACHE / "incidents.csv")
    ids = list(loader.sample_cases()["case_id"])
    return ids, [alarms_from_df(inc[inc.case_id == cid]) for cid in ids]


def note_of(res):
    return ";".join(f"{k}={v}" for k, v in res.ops.items()) + f";peak={res.peak}"


def scaling(lists):
    pooled_all = pool_alarms(lists)
    data = {k: [] for k in ALGOS}
    results = {k: {} for k in ALGOS}
    for m in SIZES:
        al = pooled_all[:m]
        for name, fn in ALGOS.items():
            med, iqr, res = time_it(fn, al)
            tracemalloc.start()
            fn(al)
            mem = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
            if med is None:
                log_row(module="D", experiment="scaling", algorithm=name, instance=f"pool{m}",
                        size=len(al), status="DNF")
                continue
            log_row(module="D", experiment="scaling", algorithm=name, instance=f"pool{m}",
                    size=len(al), size2=res.peak, time_s=med, time_iqr_s=iqr, ops=res.ops["total"],
                    mem_bytes=mem, status="OK", note=note_of(res))
            data[name].append((m, med))
            results[name][m] = res
            print(f"{name:12s} m={m:5d} time={med:.5f}s ops={res.ops['total']} peak={res.peak}")
        if all(m in results[k] for k in ALGOS):
            orders = [tuple(results[k][m].order) for k in ALGOS]
            assert orders[0] == orders[1] == orders[2], f"release orders differ at m={m}"
    lines = []
    for name, pts in data.items():
        if len(pts) < 5:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        slope, ci, r2, _ = loglog_fit(xs, ys)
        a, _, _, b = loglog_fit(xs[:4], ys[:4])
        err = abs(math.exp(b + a * math.log(xs[-1])) - ys[-1]) / ys[-1]
        lines.append(f"{name}: slope={slope:.3f} +/- {ci:.3f} (95% CI) R2={r2:.4f} "
                     f"prediction error at m={xs[-1]}: {err:.1%}")
    last = SIZES[-1]
    if all(last in results[k] for k in ALGOS):
        t = {k: data[k][-1][1] for k in ALGOS}
        lines.append(f"Linear-scan / Binary-heap time at m={last}: {t['Linear-scan'] / t['Binary-heap']:.2f}")
        lines.append(f"Binary-heap / Bucket-queue time at m={last}: {t['Binary-heap'] / t['Bucket-queue']:.2f}")
        lines.append(f"Linear-scan comparisons at m={last}: {results['Linear-scan'][last].ops['cmp']}; "
                     f"peak backlog {results['Binary-heap'][last].peak}")
    (RESULTS / "fit_D.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))


def quality(ids, lists):
    """Every sample case, all alarms, one run per algorithm (no timing)."""
    for cid, al in zip(ids, lists):
        res = {name: fn(al) for name, fn in ALGOS.items()}
        agree = len({tuple(r.order) for r in res.values()}) == 1
        m = len(al)
        span = (max(a[1] for a in al) + 1) if al else 1
        prios = len({a[2] for a in al})
        for name, r in res.items():
            log_row(module="D", experiment="quality", algorithm=name, instance=cid, size=m,
                    size2=r.peak, ops=r.ops["total"], status="OK" if agree else "FAIL",
                    note=f"distinct_priorities={prios};alarms_per_tick={m / span:.2f};"
                         f"agree={agree};" + note_of(r))
        print(cid, "quality done")


def days(ids, lists):
    """Every sample case on every campaign day, with the day's extra alarm added."""
    for cid, base in zip(ids, lists):
        for day in range(1, 8):
            al = add_day_alarms(base, day)
            res = {name: fn(al) for name, fn in ALGOS.items()}
            agree = len({tuple(r.order) for r in res.values()}) == 1
            extra_note = ""
            if day in (2, 5):
                extra_id = al[-1][0]
                r0 = res["Binary-heap"]
                extra_note = f";extra_id={extra_id};extra_released_at={r0.ticks[r0.order.index(extra_id)]}"
            for name, r in res.items():
                log_row(module="D", experiment="days", algorithm=name, instance=cid, size=len(al),
                        size2=day, ops=r.ops["total"], status="OK" if agree else "FAIL",
                        note=f"day={day};peak={r.peak};agree={agree}{extra_note}")
        print(cid, "days done")


if __name__ == "__main__":
    reset_module("D")
    ids, lists = case_lists()
    scaling(lists)
    quality(ids, lists)
    days(ids, lists)