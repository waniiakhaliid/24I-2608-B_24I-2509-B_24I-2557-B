#!/usr/bin/env python3
"""Builds validator/tests/: three valid single-case workbooks (a tier-S case, a tier-M case, a trap case) and,
for each, several broken copies (one defect each). File name: broken_<case>_<defect>__<expected rule>.xlsx
usage: python make_tests.py cases.xlsx"""
import copy
import os
import sys
from openpyxl import Workbook, load_workbook

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
CASES = {5: "S", 22: "M", 47: "X"}  # case numbers used as valid test cases


def load_all(path):
    wb = load_workbook(path, read_only=True)
    return {ws.title: [list(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}


def extract(T, cid):
    return {s: [rows[0]] + [r for r in rows[1:] if r[0] == cid] for s, rows in T.items()}


def save(T, path):
    wb = Workbook()
    wb.remove(wb.active)
    for s, rows in T.items():
        ws = wb.create_sheet(s)
        for r in rows:
            ws.append(r)
            for c in ws[ws.max_row]:
                if isinstance(c.value, str):
                    c.number_format = "@"
    wb.save(path)


def col(T, s, name):
    return T[s][0].index(name)


def rows(T, s):
    return T[s][1:]


# ---- defects: each takes the single-case tables and edits them in place --------------------------------
def d_header(T):            T["crates"][0][3] = "kg"
def d_tier(T):              T["cases"][1][col(T, "cases", "tier")] = "L" if T["cases"][1][3] != "L" else "M"
def d_dup_serial(T):
    i = col(T, "crates", "serial"); r = rows(T, "crates"); r[1][i] = r[0][i]
def d_weight(T):            rows(T, "crates")[0][col(T, "crates", "weight")] = 21
def d_capacity(T):          T["cases"][1][col(T, "cases", "capacity")] = 10 ** 6
def d_road_order(T):
    u, v = col(T, "roads", "u"), col(T, "roads", "v"); r = rows(T, "roads")[0]; r[u], r[v] = r[v], r[u]
def d_road_ref(T):          rows(T, "roads")[0][col(T, "roads", "v")] = 10 ** 5
def d_disconnect(T):
    u, v = col(T, "roads", "u"), col(T, "roads", "v"); last = len(rows(T, "locations")) - 1
    keep = [r for r in rows(T, "roads") if last not in (r[u], r[v])]
    for i, r in enumerate(keep): r[col(T, "roads", "road_no")] = i
    T["roads"] = [T["roads"][0]] + keep
def d_wave_overlap(T):
    w = rows(T, "waves"); T["waves"].append([w[0][0], w[-1][1], w[0][2]] if w[-1][1] != w[0][1] else [w[0][0], w[0][1] + 1, w[0][2]])
def d_pattern_count(T):     rows(T, "radio_patterns")[0][col(T, "radio_patterns", "count")] += 1
def d_edit_bound(T):        T["cases"][1][col(T, "cases", "edit_bound")] = 0
def d_log_symbol(T):
    r = rows(T, "radio_log")[0]; i = col(T, "radio_log", "text"); r[i] = "!" + r[i][1:]
def d_window(T):
    r = rows(T, "windows")[0]; r[col(T, "windows", "finish")] = r[col(T, "windows", "start")]
def d_tick(T):              rows(T, "incidents")[0][col(T, "incidents", "tick")] = 3
def d_tour_perm(T):
    r = rows(T, "tour"); r[1][col(T, "tour", "site_no")] = r[2][col(T, "tour", "site_no")]
def d_tour_len(T):          T["cases"][1][col(T, "cases", "tour_length")] += 1
def d_cover(T):             T["sensor_cover"].pop(1)
def d_safety(T):
    rl = rows(T, "safety_rules")[0]; names = T["safety_rules"][0]
    for nm in ("lit_1", "lit_2", "lit_3"):
        lit = rl[names.index(nm)]
        for r in rows(T, "safety_planted"):
            if r[1] == abs(lit): r[2] = 0 if lit > 0 else 1
def d_rations(T):
    r = next(r for r in rows(T, "rations") if r[col(T, "rations", "planted")] == 1); r[col(T, "rations", "planted")] = 0
def d_claim(T):             T["claims"][1][col(T, "claims", "cargo_opt")] += 1
def d_sc6_expiry(T):
    for r in rows(T, "crates"): r[col(T, "crates", "expiry")] = 999
def d_sc5_waves(T):         T["waves"] = [T["waves"][0]] + [r for r in rows(T, "waves") if r[1] < 2]
def d_trap47(T):
    for r in rows(T, "crates"):
        if r[col(T, "crates", "weight")] == 1: r[col(T, "crates", "weight")] = 20

COMMON = [("header_renamed", "V1", d_header), ("wrong_tier", "V1", d_tier), ("duplicate_serial", "V3", d_dup_serial),
          ("weight_21", "V2", d_weight), ("capacity_too_big", "V2", d_capacity), ("road_u_ge_v", "V3", d_road_order),
          ("road_unknown_location", "V3", d_road_ref), ("disconnected_network", "V4", d_disconnect),
          ("waves_overlap", "V4", d_wave_overlap), ("wrong_pattern_count", "V5", d_pattern_count),
          ("edit_bound_too_small", "V5", d_edit_bound), ("bad_log_symbol", "V2", d_log_symbol),
          ("window_finish_eq_start", "V2", d_window), ("first_tick_not_zero", "V2", d_tick),
          ("tour_not_permutation", "V6", d_tour_perm), ("wrong_tour_length", "V6", d_tour_len),
          ("cover_misses_edge", "V6", d_cover), ("safety_rule_violated", "V6", d_safety),
          ("ration_sum_wrong", "V6", d_rations)]
EXTRA = {5: [("wrong_claim", "V5", d_claim), ("outbreak_expiry_signature", "V7", d_sc6_expiry)],
         22: [("landslide_two_waves_signature", "V7", d_sc5_waves)],
         47: [("greedy_not_fooled_trap47", "V8", d_trap47)]}


def main(path):
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".xlsx"): os.remove(os.path.join(OUT, f))
    T = load_all(path)
    seed = T["cases"][1][1]
    for k in CASES:
        cid = f"{seed}-{k:02d}"
        base = extract(T, cid)
        save(base, os.path.join(OUT, f"valid_{cid}.xlsx"))
        for name, code, fn in COMMON + EXTRA[k]:
            if name in ("wrong_claim",) and CASES[k] != "S": continue
            t = copy.deepcopy(base)
            fn(t)
            save(t, os.path.join(OUT, f"broken_{cid}_{name}__{code}.xlsx"))
    print("tests written to", OUT, "-", len(os.listdir(OUT)), "files")


if __name__ == "__main__":
    main(sys.argv[1])
