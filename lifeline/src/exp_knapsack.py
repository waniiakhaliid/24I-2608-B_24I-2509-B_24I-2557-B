"""Module A experiments: scaling (5 geometric sizes) and quality on the sample."""
import math
import tracemalloc
import pandas as pd
import loader
from config import CACHE, RESULTS
from harness import time_it, log_row, reset_module
from modules.knapsack import knapsack_dp, knapsack_greedy, crate_arrays

SIZES = [100, 200, 400, 800, 1600]
FRACTION = 0.35                  # capacity = 35% of total weight (sample range 0.10-0.64)
ALGOS = {"DP-capacity": knapsack_dp, "Ratio-greedy": knapsack_greedy}
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}


def pooled(n):
    """Crates of the sampled cases joined in sample order, first n, renumbered."""
    cr = pd.read_csv(CACHE / "crates.csv")
    w, v = [], []
    for cid in loader.sample_cases()["case_id"]:
        cw, cv = crate_arrays(cr[cr.case_id == cid])
        w += cw
        v += cv
    return w[:n], v[:n]


def loglog_fit(xs, ys):
    lx, ly = [math.log(x) for x in xs], [math.log(y) for y in ys]
    n = len(xs)
    mx, my = sum(lx) / n, sum(ly) / n
    sxx = sum((a - mx) ** 2 for a in lx)
    slope = sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sxx
    icpt = my - slope * mx
    ss_res = sum((b - (icpt + slope * a)) ** 2 for a, b in zip(lx, ly))
    ss_tot = sum((b - my) ** 2 for b in ly)
    ci = T975[n - 2] * math.sqrt(ss_res / (n - 2) / sxx)
    return slope, ci, 1 - ss_res / ss_tot, icpt


def scaling():
    data = {name: [] for name in ALGOS}
    for n in SIZES:
        w, v = pooled(n)
        cap = int(FRACTION * sum(w))
        for name, fn in ALGOS.items():
            med, iqr, res = time_it(fn, w, v, cap)
            tracemalloc.start()
            fn(w, v, cap)
            mem = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
            if med is None:
                log_row(module="A", experiment="scaling", algorithm=name, instance=f"pool{n}",
                        size=n, size2=cap, status="DNF")
                continue
            log_row(module="A", experiment="scaling", algorithm=name, instance=f"pool{n}",
                    size=n, size2=cap, time_s=med, time_iqr_s=iqr, ops=res.ops,
                    mem_bytes=mem, status="OK", note=f"value={res.value}")
            data[name].append((n, med, res.value))
            print(f"{name:13s} n={n:5d} W={cap:6d} time={med:.4f}s ops={res.ops} value={res.value}")
    lines = []
    for name, pts in data.items():
        if len(pts) < 5:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        slope, ci, r2, _ = loglog_fit(xs, ys)
        # predict the last size from a fit on the first four, compare with measurement
        a, _, _, b = loglog_fit(xs[:4], ys[:4])
        pred = math.exp(b + a * math.log(xs[-1]))
        err = abs(pred - ys[-1]) / ys[-1]
        lines.append(f"{name}: slope={slope:.3f} +/- {ci:.3f} (95% CI) R2={r2:.4f} "
                     f"prediction error at n={xs[-1]}: {err:.1%}")
    if all(len(data[k]) == len(SIZES) for k in ALGOS):
        ratio = [(n, g / d) for (n, _, d), (_, _, g) in zip(data["DP-capacity"], data["Ratio-greedy"])]
        lines.append("greedy value / DP value: " + ", ".join(f"n={n}: {r:.3f}" for n, r in ratio))
    (RESULTS / "fit_A.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))


def quality():
    """DP vs greedy value on every sampled case (one run each, no timing)."""
    cr = pd.read_csv(CACHE / "crates.csv")
    for _, row in loader.sample_cases().iterrows():
        w, v = crate_arrays(cr[cr.case_id == row.case_id])
        cap = int(row.capacity)
        for name, fn in ALGOS.items():
            res = fn(w, v, cap)
            log_row(module="A", experiment="quality", algorithm=name, instance=row.case_id,
                    size=len(w), size2=cap, ops=res.ops, status="OK", note=f"value={res.value}")
        print(row.case_id, "done")


if __name__ == "__main__":
    reset_module("A")
    scaling()
    quality()