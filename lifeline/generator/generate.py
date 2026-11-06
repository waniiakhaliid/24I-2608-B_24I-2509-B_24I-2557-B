#!/usr/bin/env python3
"""LIFELINE Iteration 1 generator.   usage: python generate.py --seed <group number> --out cases.xlsx"""
import argparse
import random
import time
from openpyxl import Workbook
from common import RANGES, case_id, rng_for, scenario_of, tier_of
import crates as cr, network as nw, radio as rd, windows as wd, tour as tr, planning as pl

SHEETS = {
    "cases": ["case_id", "group_seed", "case_no", "tier", "scenario", "capacity", "target_0", "target_1",
              "target_2", "edit_bound", "tour_length", "sensor_nodes", "sensor_k", "safety_vars", "rations_target"],
    "crates": ["case_id", "crate_id", "cat", "weight", "value", "expiry", "serial"],
    "locations": ["case_id", "loc_id", "type", "penalty"],
    "roads": ["case_id", "road_no", "u", "v", "minutes", "cable"],
    "waves": ["case_id", "wave_no", "road_no"],
    "radio_log": ["case_id", "part", "text"],
    "radio_patterns": ["case_id", "pattern_no", "pattern", "count"],
    "radio_reports": ["case_id", "report_a", "report_b"],
    "windows": ["case_id", "window_id", "start", "finish", "value"],
    "incidents": ["case_id", "alarm_id", "tick", "priority"],
    "sites": ["case_id", "site_no", "x", "y"],
    "tour": ["case_id", "step", "site_no"],
    "pipeline_dims": ["case_id", "idx", "dim"],
    "drum_prices": ["case_id", "length", "price"],
    "sensor_edges": ["case_id", "u", "v"],
    "sensor_cover": ["case_id", "node"],
    "safety_rules": ["case_id", "rule_no", "lit_1", "lit_2", "lit_3"],
    "safety_planted": ["case_id", "switch", "value"],
    "rations": ["case_id", "item", "value", "planted"],
    "claims": ["case_id", "cargo_opt", "window_count_opt", "window_value_opt", "drum_opt", "tour_opt", "cover_min"],
}


def build_case(seed, k, flags, bucket):
    cid, tier, scen = case_id(seed, k), tier_of(k), scenario_of(k)
    R = RANGES[tier]
    out = {s: [] for s in SHEETS}

    # ---- crates and capacity
    r = rng_for(seed, k, "crates")
    if k == 47:
        crates, cap = cr.trap47(r, scen)
    else:
        n = r.randint(1500, 3000) if k == 46 else r.randint(*R["crates"])
        for _ in range(5000):
            crates = cr.make_crates(r, n, scen)
            if k == 46:
                cr.dock_order(crates)
            cap = cr.capacity_for(r, crates)
            if not flags.get("greedy_fail") or cr.knapsack_opt(crates, cap) > cr.greedy_value(crates, cap):
                break
        else:
            raise RuntimeError(f"case {k}: could not make greedy suboptimal")
    out["crates"] = [(cid, c["id"], c["cat"], c["weight"], c["value"], c["expiry"], c["serial"]) for c in crates]

    # ---- network
    r = rng_for(seed, k, "network")
    net = nw.make_trap48(r) if k == 48 else nw.make_network(r, scen, r.randint(*R["V"]), flags.get("detour", False))
    out["locations"] = [(cid, i, net["types"][i], net["pen"][i]) for i in range(net["V"])]
    out["roads"] = [(cid, i, u, v, m, c) for i, (u, v, m, c) in enumerate(net["edges"])]
    out["waves"] = [(cid, w, road) for w, roads in enumerate(net["waves"]) for road in roads]

    # ---- radio
    r = rng_for(seed, k, "radio")
    if k == 49:
        text, pats = rd.trap49(r)
    else:
        text = rd.gen_log(r, r.randint(*R["log"]), scen)
        pats = rd.gen_patterns(r, text)
    out["radio_log"] = [(cid, p, t) for p, t in rd.split_parts(text)]
    out["radio_patterns"] = [(cid, i, p, c) for i, p, c in pats]
    ra, rb, bound = rd.gen_reports(r, *R["report"])
    out["radio_reports"] = [(cid, ra, rb)]

    # ---- windows, incidents
    r = rng_for(seed, k, "windows")
    ws = wd.gen_windows(r, r.randint(*R["windows"]), scen, tier)
    out["windows"] = [(cid, i + 1, s, f, v) for i, (s, f, v) in enumerate(ws)]
    r = rng_for(seed, k, "incidents")
    out["incidents"] = [(cid,) + a for a in wd.gen_incidents(r, r.randint(*R["alarms"]), scen, tier)]

    # ---- sites and planted tour
    r = rng_for(seed, k, "tour")
    pts = tr.gen_sites(r, r.randint(*R["sites"]))
    tour = tr.planted_tour(pts, tier)
    tour_len = tr.closed_len(pts, tour)
    out["sites"] = [(cid, i, x, y) for i, (x, y) in enumerate(pts)]
    out["tour"] = [(cid, i, s) for i, s in enumerate(tour)]

    # ---- pipeline, drum
    r = rng_for(seed, k, "pipeline")
    out["pipeline_dims"] = [(cid, i, d) for i, d in enumerate(pl.gen_dims(r, r.randint(*R["stages"])))]
    r = rng_for(seed, k, "drum")
    prices = pl.gen_drum(r, r.randint(*R["drum"]))
    out["drum_prices"] = [(cid, j + 1, p) for j, p in enumerate(prices)]

    # ---- sensors, safety, rations
    r = rng_for(seed, k, "sensors")
    sn = r.randint(*R["sensors"])
    sk, cover, sedges = pl.gen_sensors(r, sn)
    out["sensor_edges"] = [(cid, u, v) for u, v in sedges]
    out["sensor_cover"] = [(cid, c) for c in cover]
    r = rng_for(seed, k, "safety")
    m = r.randint(*R["switches"])
    planted, rules = pl.gen_safety(r, m, pl.rule_count(r, m, bucket))
    out["safety_rules"] = [(cid, i + 1, *lits) for i, lits in enumerate(rules)]
    out["safety_planted"] = [(cid, j + 1, v) for j, v in enumerate(planted)]
    r = rng_for(seed, k, "rations")
    vals, flag, target = pl.gen_rations(r, r.randint(*R["rations"]))
    out["rations"] = [(cid, i, v, f) for i, (v, f) in enumerate(zip(vals, flag))]

    out["cases"] = [(cid, seed, k, tier, scen, cap, *net["targets"], bound, tour_len, sn, sk, m, target)]

    # ---- claims (tier S only, exhaustive/exact optima)
    if tier == "S":
        wc, wv = pl.window_opts(ws)
        out["claims"] = [(cid, cr.knapsack_opt(crates, cap), wc, wv, pl.drum_opt(prices),
                          tr.closed_len(pts, tr.optimal_tour(pts)[0]), pl.min_cover(sn, sedges))]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="group number from the group-selection sheet")
    ap.add_argument("--out", default="cases.xlsx")
    a = ap.parse_args()
    t0 = time.time()
    sched = ["low"] * 6 + ["mid"] * 12 + ["high"] * 8            # variety rule 3 over the 26 cases of tiers M and L
    random.Random(f"lifeline|{a.seed}|buckets").shuffle(sched)
    buckets = {k: sched[k - 20] if 20 <= k <= 45 else "any" for k in range(50)}
    allrows = {s: [] for s in SHEETS}
    for k in range(50):
        flags = {"greedy_fail": k < 20 and k % 3 == 0,                 # variety rule 1 (7 cases)
                 "detour": k < 20 and k % 6 in (0, 2, 3, 5)}            # variety rule 2 (13 cases)
        rows = build_case(a.seed, k, flags, buckets[k])
        for s in SHEETS:
            allrows[s].extend(rows[s])
        print(f"case {k:02d} ok ({time.time() - t0:5.1f}s)", flush=True)
    wb = Workbook()
    wb.remove(wb.active)
    for s, header in SHEETS.items():
        ws = wb.create_sheet(s)
        ws.append(header)
        for row in allrows[s]:
            ws.append(list(row))
        for rw in ws.iter_rows(min_row=2):
            for c in rw:
                if isinstance(c.value, str):
                    c.number_format = "@"                                # text cells stay text
    wb.save(a.out)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
