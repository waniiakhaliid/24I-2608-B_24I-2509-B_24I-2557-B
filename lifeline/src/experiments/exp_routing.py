"""Module B experiments: scaling on random connected maps, and the sample cases on all 7 days."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # makes src/ importable

import math
import tracemalloc
import loader
from config import RESULTS, RANDOM_SEED
from harness import time_it, log_row, reset_module
from stats import loglog_fit
from graphgen import random_graph
from modules.routing import (build_graph, dijkstra, bellman_ford, bfs, route, walk,
                             case_graph)

SIZES = [250, 500, 1000, 2000, 4000]
ALGOS = {"Heap-Dijkstra": dijkstra, "Bellman-Ford": bellman_ford, "BFS-levels": bfs}


def scaling():
    data = {k: [] for k in ALGOS}
    for V in SIZES:
        pen, roads = random_graph(V, RANDOM_SEED + V)          # seed = 84 + V
        adj = build_graph(pen, roads)
        E = len(roads)
        d_ref = dijkstra(adj, 0)
        assert d_ref.dist == bellman_ford(adj, 0).dist, "Dijkstra and Bellman-Ford disagree"
        for name, fn in ALGOS.items():
            med, iqr, res = time_it(fn, adj, 0)
            tracemalloc.start()
            fn(adj, 0)
            mem = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
            note = ";".join(f"{k}={v}" for k, v in res.ops.items())
            if med is None:
                log_row(module="B", experiment="scaling", algorithm=name, instance=f"rand{V}",
                        size=V, size2=E, status="DNF", note=note)
                continue
            log_row(module="B", experiment="scaling", algorithm=name, instance=f"rand{V}",
                    size=V, size2=E, time_s=med, time_iqr_s=iqr, ops=res.ops["total"],
                    mem_bytes=mem, status="OK", note=note)
            data[name].append((V, med))
            print(f"{name:14s} V={V:5d} E={E:6d} time={med:.5f}s ops={res.ops['total']} {note}")
    lines = []
    for name, pts in data.items():
        if len(pts) < 5:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        slope, ci, r2, _ = loglog_fit(xs, ys)
        a, _, _, b = loglog_fit(xs[:4], ys[:4])
        err = abs(math.exp(b + a * math.log(xs[-1])) - ys[-1]) / ys[-1]
        lines.append(f"{name}: slope={slope:.3f} +/- {ci:.3f} (95% CI) R2={r2:.4f} "
                     f"prediction error at V={xs[-1]}: {err:.1%}")
    if all(len(data[k]) == len(SIZES) for k in ("Heap-Dijkstra", "Bellman-Ford")):
        lines.append(f"Bellman-Ford / Dijkstra time at V={SIZES[-1]}: "
                     f"{data['Bellman-Ford'][-1][1] / data['Heap-Dijkstra'][-1][1]:.2f}")
    (RESULTS / "fit_B.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))


def cases():
    """Every sample case on every day: reachability, cheapest cost, fewest-roads cost."""
    for cid in loader.sample_cases()["case_id"]:
        case = loader.load_case(cid)
        for day in range(1, 8):
            adj, target, closed = case_graph(case, day)
            V = len(adj)
            E_open = sum(len(a) for a in adj) // 2
            d, b, f = dijkstra(adj, 0), bellman_ford(adj, 0), bfs(adj, 0)
            cost = d.dist[target]
            fp = route(f.parent, f.hops, 0, target)
            fewest = None if fp is None else walk(adj, fp)[0]
            agree = d.dist == b.dist
            reach = sum(x is not None for x in d.dist)
            note = (f"day={day};target={target};cost={cost};hops={f.hops[target]};"
                    f"fewest_roads_cost={fewest};reachable={reach};agree={agree}")
            status = "OK" if agree else "FAIL"
            log_row(module="B", experiment="cases", algorithm="Heap-Dijkstra", instance=cid,
                    size=V, size2=E_open, ops=d.ops["total"], status=status, note=note)
            log_row(module="B", experiment="cases", algorithm="Bellman-Ford", instance=cid,
                    size=V, size2=E_open, ops=b.ops["total"], status=status,
                    note=f"day={day};passes={b.ops['passes']}")
            log_row(module="B", experiment="cases", algorithm="BFS-levels", instance=cid,
                    size=V, size2=E_open, ops=f.ops["total"], status="OK", note=note)
        print(cid, "done")


if __name__ == "__main__":
    reset_module("B")
    scaling()
    cases()