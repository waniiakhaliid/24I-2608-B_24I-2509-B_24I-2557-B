#!/usr/bin/env python3
"""LIFELINE validator. Recomputes everything from the sheets (trusts no field).
usage: uv run python lifeline/validator/validate.py lifeline/cases.xlsx            full check of the 50-case workbook
       python validate.py file.xlsx --partial   check only the cases present (used for validator/tests)
Prints PASS or the broken rules (V1..V8) for every case. Exit code 0 only if everything passes."""
import re
import sys
import heapq
import itertools
from collections import defaultdict, deque
from fractions import Fraction
from openpyxl import load_workbook

ALPHA = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
S, I = "s", "i"
SCHEMA = {
    "cases": (["case_id", "group_seed", "case_no", "tier", "scenario", "capacity", "target_0", "target_1", "target_2",
               "edit_bound", "tour_length", "sensor_nodes", "sensor_k", "safety_vars", "rations_target"],
              [S, I, I, S, I, I, I, I, I, I, I, I, I, I, I]),
    "crates": (["case_id", "crate_id", "cat", "weight", "value", "expiry", "serial"], [S] + [I] * 6),
    "locations": (["case_id", "loc_id", "type", "penalty"], [S, I, S, I]),
    "roads": (["case_id", "road_no", "u", "v", "minutes", "cable"], [S] + [I] * 5),
    "waves": (["case_id", "wave_no", "road_no"], [S, I, I]),
    "radio_log": (["case_id", "part", "text"], [S, I, S]),
    "radio_patterns": (["case_id", "pattern_no", "pattern", "count"], [S, I, S, I]),
    "radio_reports": (["case_id", "report_a", "report_b"], [S, S, S]),
    "windows": (["case_id", "window_id", "start", "finish", "value"], [S] + [I] * 4),
    "incidents": (["case_id", "alarm_id", "tick", "priority"], [S] + [I] * 3),
    "sites": (["case_id", "site_no", "x", "y"], [S] + [I] * 3),
    "tour": (["case_id", "step", "site_no"], [S, I, I]),
    "pipeline_dims": (["case_id", "idx", "dim"], [S, I, I]),
    "drum_prices": (["case_id", "length", "price"], [S, I, I]),
    "sensor_edges": (["case_id", "u", "v"], [S, I, I]),
    "sensor_cover": (["case_id", "node"], [S, I]),
    "safety_rules": (["case_id", "rule_no", "lit_1", "lit_2", "lit_3"], [S] + [I] * 4),
    "safety_planted": (["case_id", "switch", "value"], [S, I, I]),
    "rations": (["case_id", "item", "value", "planted"], [S, I, I, I]),
    "claims": (["case_id", "cargo_opt", "window_count_opt", "window_value_opt", "drum_opt", "tour_opt", "cover_min"],
               [S] + [I] * 6),
}
RANGE = {  # tier -> field -> (lo, hi)
    "S": dict(crates=(8, 20), V=(6, 12), log=(200, 500), report=(10, 30), windows=(8, 20), alarms=(10, 40),
              sites=(5, 9), stages=(4, 8), drum=(5, 14), sensors=(6, 14), switches=(6, 15), rations=(8, 20)),
    "M": dict(crates=(40, 200), V=(30, 150), log=(2000, 10000), report=(30, 150), windows=(50, 300),
              alarms=(200, 1000), sites=(10, 16), stages=(15, 60), drum=(40, 200), sensors=(20, 40),
              switches=(20, 50), rations=(24, 40)),
    "L": dict(crates=(500, 1500), V=(500, 2000), log=(20000, 100000), report=(200, 1000), windows=(1000, 3000),
              alarms=(2000, 5000), sites=(200, 500), stages=(100, 300), drum=(500, 2000), sensors=(100, 400),
              switches=(20, 50), rations=(50, 100)),
}
RANGE["X"] = RANGE["L"]
MODULES = {"crates": ["crates"], "network": ["locations", "roads", "waves"],
           "radio": ["radio_log", "radio_patterns", "radio_reports"], "windows": ["windows"],
           "incidents": ["incidents"], "tour": ["sites", "tour"], "pipeline": ["pipeline_dims", "drum_prices"],
           "sensors": ["sensor_edges", "sensor_cover"], "safety": ["safety_rules", "safety_planted"],
           "rations": ["rations"]}


# ------------------------------------------------------------------ helpers (independent of the generator)
def bfs(V, adj, src=0):
    d = [-1] * V
    d[src] = 0
    q = deque([src])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if d[v] < 0:
                d[v] = d[u] + 1
                q.append(v)
    return d


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return prev[-1]


def occurrences(text, p):
    n, m = len(text), len(p)
    return sum(1 for i in range(n - m + 1) if text.startswith(p, i)) if n * m < 2000 else _find_all(text, p)


def _find_all(text, p):
    c, i = 0, text.find(p)
    while i >= 0:
        c += 1
        i = text.find(p, i + 1)
    return c


def knap(items, cap):
    best = [0] * (cap + 1)
    for w, v in items:
        for j in range(cap, w - 1, -1):
            best[j] = max(best[j], best[j - w] + v)
    return best[cap]


def greedy(items, cap):
    """items (id, w, v): decreasing value/weight by exact cross-multiplication, id ascending on ties."""
    order = sorted(items, key=lambda t: (-Fraction(t[2], t[1]), t[0]))
    left, tot = cap, 0
    for _, w, v in order:
        if w <= left:
            left -= w
            tot += v
    return tot


def route_info(V, nbr, pen):
    """nbr[u] = [(v, minutes)]; returns hops, cheapest cost, cheapest cost among fewest-road routes."""
    hop = [-1] * V
    hop[0] = 0
    order, q = [0], deque([0])
    while q:
        u = q.popleft()
        for v, _ in nbr[u]:
            if hop[v] < 0:
                hop[v] = hop[u] + 1
                order.append(v)
                q.append(v)
    INF = float("inf")
    dist = [INF] * V
    dist[0] = 0
    pq = [(0, 0)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, m in nbr[u]:
            if d + m + pen[v] < dist[v]:
                dist[v] = d + m + pen[v]
                heapq.heappush(pq, (dist[v], v))
    fw = [INF] * V
    fw[0] = 0
    for u in order:
        for v, m in nbr[u]:
            if hop[v] == hop[u] + 1:
                fw[v] = min(fw[v], fw[u] + m + pen[v])
    return hop, dist, fw


def man(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def best_tour(pts):
    n = len(pts)
    best = None
    for perm in itertools.permutations(range(1, n)):
        t = (0,) + perm
        L = sum(man(pts[t[i]], pts[t[(i + 1) % n]]) for i in range(n))
        if best is None or L < best:
            best = L
    return best


def min_cover(n, edges):
    em = [(1 << u) | (1 << v) for u, v in edges]
    best = n
    for m in range(1 << n):
        c = bin(m).count("1")
        if c < best and all(m & e for e in em):
            best = c
    return best


def window_opts(ws):
    ws = sorted(ws, key=lambda w: (w[1], w[0]))
    cnt, last = 0, -1
    for s, f, _ in ws:
        if s >= last:
            cnt, last = cnt + 1, f
    best = [0] * len(ws)  # best[i] = best value using windows 0..i
    for i, (s, f, v) in enumerate(ws):
        prev = 0
        for j in range(i - 1, -1, -1):
            if ws[j][1] <= s:
                prev = best[j]
                break
        best[i] = max(best[i - 1] if i else 0, prev + v)
    return cnt, best[-1]


def drum(p):
    r = [0] * (len(p) + 1)
    for j in range(1, len(p) + 1):
        r[j] = max(p[i - 1] + r[j - i] for i in range(1, j + 1))
    return r[-1]


# ------------------------------------------------------------------ loading + V1 (workbook level)
def load(path):
    wb = load_workbook(path, read_only=True)
    glob, tables = [], {}
    names = [ws.title for ws in wb.worksheets]
    if names != list(SCHEMA):
        glob.append(("V1", f"sheets must be exactly {list(SCHEMA)} in order, got {names}"))
    for ws in wb.worksheets:
        if ws.title not in SCHEMA:
            continue
        rows = list(ws.iter_rows(values_only=True))
        head, kinds = SCHEMA[ws.title]
        if list(rows[0] if rows else []) != head:
            glob.append(("V1", f"sheet {ws.title}: header must be {head}"))
            continue
        body, prev = [], None
        for r in rows[1:]:
            if all(c is None for c in r):
                glob.append(("V1", f"sheet {ws.title}: empty row"))
                continue
            for c, kind, h in zip(r, kinds, head):
                ok = isinstance(c, str) if kind == S else (isinstance(c, int) and not isinstance(c, bool))
                if not ok:
                    glob.append(("V1", f"sheet {ws.title}: column {h} has {c!r} (expected {'text' if kind == S else 'integer'})"))
                    break
            else:
                key = (r[0], r[1] if isinstance(r[1], int) else 0)
                if prev is not None and key < prev:
                    glob.append(("V1", f"sheet {ws.title}: rows not sorted by case_id then second column"))
                prev = key
                body.append(dict(zip(head, r)))
                continue
        tables[ws.title] = body
    return tables, glob


# ------------------------------------------------------------------ per-case checks
def check_case(cid, c, D, out):
    def bad(code, msg):
        out.append((code, msg))

    k, tier, scen = c["case_no"], c["tier"], c["scenario"]
    R = RANGE[tier if tier in RANGE else "S"]
    # V1: identity
    m = re.fullmatch(r"(\d+)-(\d\d)", cid)
    if not m or int(m.group(1)) != c["group_seed"] or int(m.group(2)) != k:
        bad("V1", "case_id must be <group_seed>-<case_no as 2 digits>")
    if not 0 <= k <= 49:
        bad("V1", "case_no outside 0..49")
        return
    if tier != ("S" if k < 20 else "M" if k < 40 else "L" if k < 46 else "X") or scen != k % 6 + 1:
        bad("V1", "wrong tier or scenario for case_no")
    crates, loc, roads = D("crates"), D("locations"), D("roads")
    n, V, E = len(crates), len(loc), len(roads)
    # ---------- V2 / V3: crates
    lo, hi = (12, 60) if k == 47 else (1500, 3000) if k == 46 else R["crates"]
    if not lo <= n <= hi:
        bad("V2", f"{n} crates outside {lo}..{hi}")
    if [x["crate_id"] for x in crates] != list(range(1, n + 1)):
        bad("V3", "crate_id must run 1..n")
    for x in crates:
        if not (0 <= x["cat"] <= 4 and 1 <= x["weight"] <= 20 and 10 <= x["value"] <= 100 and 0 <= x["expiry"] <= 999
                and 10_000_000 <= x["serial"] <= 99_999_999):
            bad("V2", f"crate {x['crate_id']} has a field out of range")
            break
    if len({x["serial"] for x in crates}) != n:
        bad("V3", "serials not distinct")
    W = sum(x["weight"] for x in crates)
    cap = c["capacity"]
    if cap < 1 or 10 * cap < W or 10 * cap > 7 * W:
        bad("V2", f"capacity {cap} not within 10%..70% of total weight {W}")
    # ---------- locations / roads
    if not R["V"][0] <= V <= R["V"][1] and not (k == 48 and 1500 <= V <= 3000):
        bad("V2", f"V={V} outside range")
    if not V - 1 <= E <= 3 * V:
        bad("V2", f"E={E} outside V-1..3V")
    if [x["loc_id"] for x in loc] != list(range(V)):
        bad("V3", "loc_id must run 0..V-1")
    if not loc or loc[0]["type"] != "D" or loc[0]["penalty"] != 0:
        bad("V2", "location 0 must be the HQ (type D, penalty 0)")
    if any(x["type"] not in ("D", "S", "H", "J") or x["penalty"] not in (0, 1, 2, 4, 6) for x in loc):
        bad("V2", "bad location type or penalty")
    types = [x["type"] for x in loc]
    pen = [x["penalty"] for x in loc]
    if "S" not in types or "H" not in types:
        bad("V2", "need at least one shelter and one hospital")
    if [x["road_no"] for x in roads] != list(range(E)):
        bad("V3", "road_no must run 0..E-1")
    pairs = set()
    refs_ok = True
    for x in roads:
        if not (0 <= x["u"] < x["v"] < V):
            bad("V3", f"road {x['road_no']}: need 0 <= u < v < V"); refs_ok = False
            break
        if not (1 <= x["minutes"] <= 60 and 1 <= x["cable"] <= 100):
            bad("V2", f"road {x['road_no']}: minutes/cable out of range")
            break
    if refs_ok:
        pairs = {(x["u"], x["v"]) for x in roads}
        if len(pairs) != E:
            bad("V3", "repeated road pair")
    adj = [[] for _ in range(V)]
    nbr = [[] for _ in range(V)]
    if refs_ok:
        for x in roads:
            adj[x["u"]].append(x["v"]); adj[x["v"]].append(x["u"])
            nbr[x["u"]].append((x["v"], x["minutes"])); nbr[x["v"]].append((x["u"], x["minutes"]))
    hop = bfs(V, adj) if refs_ok else [-1] * V
    if min(hop) < 0:
        bad("V4", "network is not connected before closures")
    # waves
    wv = defaultdict(list)
    for x in D("waves"):
        wv[x["wave_no"]].append(x["road_no"])
    allw = [r for v in wv.values() for r in v]
    if sorted(wv) != list(range(len(wv))) or not 2 <= len(wv) <= 5:
        bad("V2", "waves must be numbered 0.. and there must be 2..5 of them")
    if any(not 0 <= r < E for r in allw):
        bad("V3", "wave refers to a road that does not exist")
    if len(allw) != len(set(allw)):
        bad("V4", "waves are not disjoint")
    if any(not 1 <= len(v) <= max(1, E // 4) for v in wv.values()):
        bad("V4", "a wave has more than max(1, floor(E/4)) roads")
    tg = [c["target_0"], c["target_1"], c["target_2"]]
    if any(not 0 < t < V for t in tg):
        bad("V3", "target does not exist or is the HQ")
        tg = []
    elif len(set(tg)) != 3 or any(types[t] not in ("S", "H") for t in tg):
        bad("V2", "targets must be three distinct shelters/hospitals")
    # ---------- radio
    parts = sorted(D("radio_log"), key=lambda x: x["part"])
    if [x["part"] for x in parts] != list(range(1, len(parts) + 1)):
        bad("V5", "log parts must be numbered 1,2,...")
    if any(len(x["text"]) > 10000 for x in parts):
        bad("V5", "a log cell holds more than 10,000 symbols")
    text = "".join(x["text"] for x in parts)
    if set(text) - ALPHA:
        bad("V2", "log has symbols outside the 38-symbol alphabet")
    lr = (50000, 100000) if k == 49 else R["log"]
    if not lr[0] <= len(text) <= lr[1]:
        bad("V2", f"log length {len(text)} outside {lr}")
    pats = sorted(D("radio_patterns"), key=lambda x: x["pattern_no"])
    if [x["pattern_no"] for x in pats] != list(range(6)) or [len(x["pattern"]) for x in pats] != [2, 4, 8, 12, 20, 40]:
        bad("V3", "need exactly six patterns, numbers 0..5, of lengths 2,4,8,12,20,40")
    cnts = [occurrences(text, x["pattern"]) for x in pats]
    if cnts != [x["count"] for x in pats]:
        bad("V5", f"pattern counts wrong (recomputed {cnts})")
    if sum(v > 0 for v in cnts) < 2 or all(v > 0 for v in cnts):
        bad("V2", "at least two patterns must occur and at least one must not")
    rep = D("radio_reports")
    if len(rep) != 1:
        bad("V3", "exactly one radio_reports row per case")
    else:
        a, b = rep[0]["report_a"], rep[0]["report_b"]
        if set(a + b) - ALPHA or not all(R["report"][0] <= len(z) <= R["report"][1] for z in (a, b)):
            bad("V2", "report symbols or length out of range")
        d = edit_distance(a, b)
        if not d <= c["edit_bound"] <= len(a) + len(b):
            bad("V5", f"edit_bound {c['edit_bound']} must lie in [{d}, {len(a) + len(b)}]")
    # ---------- windows, incidents
    ws = D("windows")
    if not R["windows"][0] <= len(ws) <= R["windows"][1]:
        bad("V2", "window count out of range")
    if [x["window_id"] for x in ws] != list(range(1, len(ws) + 1)):
        bad("V3", "window_id must run 1..")
    wl = [(x["start"], x["finish"], x["value"]) for x in ws]
    if any(not (0 <= s < f <= 1440 and 5 <= f - s <= 480 and 1 <= v <= 100) for s, f, v in wl):
        bad("V2", "a window violates 0<=start<finish<=1440, duration 5..480, value 1..100")
    if len(wl) >= 8 and sum(1 for a in wl for b in wl if a is not b and a[1] == b[0]) < 2:
        bad("V2", "fewer than two touching window pairs")
    inc = D("incidents")
    pr = [x["priority"] for x in inc]
    tk = [x["tick"] for x in inc]
    if not R["alarms"][0] <= len(inc) <= R["alarms"][1]:
        bad("V2", "alarm count out of range")
    if [x["alarm_id"] for x in inc] != list(range(1, len(inc) + 1)):
        bad("V3", "alarm_id must run 1..")
    if not tk or tk[0] != 0 or any(b < a for a, b in zip(tk, tk[1:])):
        bad("V2", "ticks must start at 0 and never decrease")
    if any(not 1 <= p <= 10 for p in pr):
        bad("V2", "priority outside 1..10")
    rate = len(inc) / (tk[-1] + 1) if tk else 0
    if tier in ("M", "L") and not (1.2 <= rate <= 1.8 and len(set(pr)) >= 6 and 1 in pr):
        bad("V2", f"alarms/tick {rate:.3f} must be 1.2..1.8 with >=6 distinct priorities including 1")
    # ---------- sites, tour (V6)
    st = D("sites")
    pts = [(x["x"], x["y"]) for x in st]
    if not R["sites"][0] <= len(pts) <= R["sites"][1] or [x["site_no"] for x in st] != list(range(len(pts))):
        bad("V3", "site count out of range or site_no not 0..n-1")
    if len(set(pts)) != len(pts) or any(not (0 <= x <= 999 and 0 <= y <= 999) for x, y in pts):
        bad("V2", "sites must be distinct and inside 0..999")
    tr = [x["site_no"] for x in sorted(D("tour"), key=lambda x: x["step"])]
    tour_ok = sorted(tr) == list(range(len(pts))) and tr[:1] == [0]
    if not tour_ok:
        bad("V6", "planted tour is not a permutation of all sites starting at site 0")
    else:
        tl = sum(man(pts[tr[i]], pts[tr[(i + 1) % len(tr)]]) for i in range(len(tr)))
        if tl != c["tour_length"]:
            bad("V6", f"tour_length {c['tour_length']} != recomputed closed length {tl}")
        if tier in ("L", "X"):
            ref = []
            for high in (False, True):
                un, t, cur = set(range(1, len(pts))), [0], 0
                while un:
                    cur = min(un, key=lambda j: (man(pts[cur], pts[j]), -j if high else j))
                    un.remove(cur); t.append(cur)
                ref.append(sum(man(pts[t[i]], pts[t[(i + 1) % len(t)]]) for i in range(len(t))))
            if tl > min(ref):
                bad("V6", f"tour longer than the nearest-neighbour tour ({tl} > {min(ref)})")
    # ---------- pipeline, drum
    dims = D("pipeline_dims")
    if [x["idx"] for x in dims] != list(range(len(dims))) or not R["stages"][0] + 1 <= len(dims) <= R["stages"][1] + 1 \
            or any(not 2 <= x["dim"] <= 100 for x in dims):
        bad("V2", "pipeline_dims: idx 0..n, n in range, dims 2..100")
    dr = sorted(D("drum_prices"), key=lambda x: x["length"])
    p = [x["price"] for x in dr]
    if [x["length"] for x in dr] != list(range(1, len(dr) + 1)) or not R["drum"][0] <= len(dr) <= R["drum"][1] \
            or any(not 1 <= v <= 500 for v in p):
        bad("V2", "drum_prices: lengths 1..L, L in range, prices 1..500")
    elif all(p[j - 1] * 1 == j * p[0] for j in range(1, len(p) + 1)):
        bad("V2", "drum prices are all proportional to length")
    # ---------- sensors (V6)
    sn = c["sensor_nodes"]
    se = [(x["u"], x["v"]) for x in D("sensor_edges")]
    cov = [x["node"] for x in D("sensor_cover")]
    if not R["sensors"][0] <= sn <= R["sensors"][1]:
        bad("V2", "sensor_nodes out of range")
    if any(not 0 <= u < v < sn for u, v in se) or len(set(se)) != len(se) or len(se) < sn - 1:
        bad("V3", "sensor edges: need 0<=u<v<nodes, no repeats, at least n-1 edges")
    if len(set(cov)) != len(cov) or any(not 0 <= x < sn for x in cov) or len(cov) != c["sensor_k"] or not 2 <= len(cov) <= sn / 2:
        bad("V6", "cover: sensor_k distinct existing nodes with 2 <= k <= n/2")
    elif any(u not in cov and v not in cov for u, v in se):
        bad("V6", "planted cover misses an edge")
    # ---------- safety (V6)
    mvars = c["safety_vars"]
    rules = D("safety_rules")
    asg = {x["switch"]: x["value"] for x in D("safety_planted")}
    if not R["switches"][0] <= mvars <= R["switches"][1] or sorted(asg) != list(range(1, mvars + 1)) or any(v not in (0, 1) for v in asg.values()):
        bad("V6", "safety_planted must give 0/1 for switches 1..safety_vars")
    elif [x["rule_no"] for x in rules] != list(range(1, len(rules) + 1)):
        bad("V3", "rule_no must run 1..")
    else:
        if not 2.0 <= len(rules) / mvars <= 6.0:
            bad("V2", f"rules per switch {len(rules) / mvars:.2f} outside 2.0..6.0")
        for x in rules:
            lits = [x["lit_1"], x["lit_2"], x["lit_3"]]
            if 0 in lits or len({abs(z) for z in lits}) != 3 or any(abs(z) > mvars for z in lits):
                bad("V2", f"rule {x['rule_no']}: three non-zero literals on three different switches"); break
            if not any((z > 0 and asg[abs(z)] == 1) or (z < 0 and asg[abs(z)] == 0) for z in lits):
                bad("V6", f"planted assignment violates rule {x['rule_no']}"); break
    # ---------- rations (V6)
    rt = D("rations")
    if [x["item"] for x in rt] != list(range(len(rt))) or not R["rations"][0] <= len(rt) <= R["rations"][1] \
            or any(not 1 <= x["value"] <= 1000 or x["planted"] not in (0, 1) for x in rt):
        bad("V2", "rations: items 0.., count in range, values 1..1000, planted 0/1")
    elif c["rations_target"] <= 0 or sum(x["value"] for x in rt if x["planted"]) != c["rations_target"]:
        bad("V6", "planted rations do not sum to rations_target")
    # ---------- V5 claims (tier S)
    cl = D("claims")
    if tier == "S":
        if len(cl) != 1:
            bad("V5", "tier S needs exactly one claims row")
        elif not out_has(out, "V2", "V3", "V6"):
            wc, wvv = window_opts(wl)
            exp = {"cargo_opt": knap([(x["weight"], x["value"]) for x in crates], cap), "window_count_opt": wc,
                   "window_value_opt": wvv, "drum_opt": drum(p), "tour_opt": best_tour(pts), "cover_min": min_cover(sn, se)}
            for key, val in exp.items():
                if cl[0][key] != val:
                    bad("V5", f"claim {key}={cl[0][key]} but recomputed {val}")
    elif cl:
        bad("V5", "claims only exist for tier S")
    # ---------- V7 signature rules (cases 0..45)
    cats = [x["cat"] for x in crates]
    pct = lambda cs: 100 * sum(z in cs for z in cats) / n
    avg = 2 * E / V if V else 0
    nw_ = len(wv)
    if k < 46:
        if scen == 1:
            if not 2.2 <= avg <= 3.2: bad("V7", f"delta: average degree {avg:.2f} not in 2.2..3.2")
            if 100 * sum(q >= 2 for q in pen) < 40 * V: bad("V7", "delta: <40% locations with penalty >= 2")
            if nw_ < 3: bad("V7", "delta: fewer than 3 waves")
            if pct((0, 1)) < 55: bad("V7", "delta: food+water crates < 55%")
        if scen == 2:
            if not 2.0 <= avg <= 2.6: bad("V7", f"mountain: average degree {avg:.2f} not in 2.0..2.6")
            if pct((2, 3)) < 45: bad("V7", "mountain: medicine+tool crates < 45%")
            if pr and sum(pr) < 6 * len(pr): bad("V7", "mountain: mean alarm priority < 6.0")
        if scen == 3:
            if 4 * types.count("S") < V: bad("V7", "cyclone: shelters < 25% of locations")
            if nw_ < 3: bad("V7", "cyclone: fewer than 3 waves")
            from bisect import bisect_left, bisect_right
            sts, fns = sorted(w[0] for w in wl), sorted(w[1] for w in wl)
            tot = sum(len(wl) - 1 - bisect_right(fns, s) - (len(wl) - bisect_left(sts, f)) for s, f, _ in wl)
            if tot < 2 * len(wl): bad("V7", "cyclone: windows overlap fewer than 2 others on average")
            if len(set(text)) < 30: bad("V7", "cyclone: log uses fewer than 30 symbols")
        if scen == 4:
            if avg < 3.5: bad("V7", f"urban: average degree {avg:.2f} < 3.5")
            if tier in ("M", "L") and rate < 1.5: bad("V7", "urban: fewer than 1.5 alarms per tick")
            if pct((4,)) < 10: bad("V7", "urban: rare crates < 10%")
        if scen == 5:
            if avg > 2.4 or max((len(a) for a in adj), default=0) > 4: bad("V7", "landslide: degree rule (avg <= 2.4, max <= 4)")
            if max(hop) < V // 4: bad("V7", "landslide: farthest location closer than floor(V/4)")
            if nw_ < 3: bad("V7", "landslide: fewer than 3 waves")
            if tg and refs_ok:
                a2 = [[] for _ in range(V)]
                closed = set(allw)
                for x in roads:
                    if x["road_no"] not in closed:
                        a2[x["u"]].append(x["v"]); a2[x["v"]].append(x["u"])
                h2 = bfs(V, a2)
                if all(h2[t] >= 0 for t in tg): bad("V7", "landslide: union of waves leaves every target reachable")
        if scen == 6:
            if pct((1, 2)) < 55: bad("V7", "outbreak: medicine+water crates < 55%")
            if 2 * sum(x["expiry"] <= 300 for x in crates) < n: bad("V7", "outbreak: fewer than half of the crates expire by hour 300")
            if text and 4 * max(text.count(ch) for ch in set(text)) < len(text): bad("V7", "outbreak: no symbol is >= 25% of the log")
    # ---------- V8 traps
    if k == 46:
        seqs = [[x["value"] for x in crates], [x["weight"] for x in crates], [x["expiry"] for x in crates],
                [x["serial"] for x in crates], [Fraction(x["value"], x["weight"]) for x in crates]]
        mono = sum(all(a <= b for a, b in zip(s, s[1:])) or all(a >= b for a, b in zip(s, s[1:])) for s in seqs)
        if mono < 3: bad("V8", f"trap 46: only {mono} of 5 fields monotone in crate_id order")
    if k == 47 and crates:
        items = [(x["crate_id"], x["weight"], x["value"]) for x in crates]
        g, o = greedy(items, cap), knap([(w, v) for _, w, v in items], cap)
        if 100 * g > 60 * o: bad("V8", f"trap 47: greedy reaches {g}/{o} > 60% of optimum")
    if k == 48 and refs_ok and min(hop) >= 0 and tg:
        _, dist, fw = route_info(V, nbr, pen)
        if not any(2 * fw[t] >= 3 * dist[t] for t in tg): bad("V8", "trap 48: no target whose fewest-road routes cost >= 1.5x the cheapest")
        far = max(range(V), key=lambda i: hop[i])
        if max(bfs(V, adj, far)) < 500: bad("V8", "trap 48: longest distance below 500 roads")
        if not 1500 <= V <= 3000: bad("V8", "trap 48: V outside 1500..3000")
    if k == 49 and text:
        top = max(text.count(ch) for ch in set(text))
        if 100 * top < 90 * len(text): bad("V8", "trap 49: less than 90% of the log repeats one block (checked for block length 1)")
        near = 0
        for x in pats:
            mm = len(x["pattern"])
            hits = _find_all(text, x["pattern"][:-1])
            if 2 * hits >= len(text) - mm + 1: near += 1
        if near < 4: bad("V8", f"trap 49: only {near} patterns have a prefix matching at >= half of all positions")
    return {"types": types, "tg": tg, "V": V, "pen": pen, "nbr": nbr, "n": n,
            "ratio": len(rules) / mvars if mvars else 0, "k": k}


def out_has(out, *codes):
    return any(c in codes for c, _ in out)


# ------------------------------------------------------------------ driver
def validate(path, partial=False):
    tables, glob = load(path)
    res = {"global": list(glob)}
    if glob and any(c == "V1" and "sheet" in m and "header" in m for c, m in glob):
        return res
    by = {s: defaultdict(list) for s in SCHEMA}
    for s, rows in tables.items():
        for r in rows:
            by[s][r["case_id"]].append(r)
    cids = [r["case_id"] for r in tables.get("cases", [])]
    if len(set(cids)) != len(cids):
        res["global"].append(("V1", "duplicate case_id in sheet cases"))
    if not partial and len(cids) != 50:
        res["global"].append(("V1", f"expected 50 cases, found {len(cids)}"))
    for s in SCHEMA:
        for cid in by[s]:
            if cid not in cids:
                res["global"].append(("V3", f"sheet {s}: case_id {cid} has no row in sheet cases"))
    seeds = {r["group_seed"] for r in tables.get("cases", [])}
    if len(seeds) > 1:
        res["global"].append(("V1", "group_seed differs between cases"))
    info = {}
    for row in tables.get("cases", []):
        cid = row["case_id"]
        errs = []
        try:
            info[cid] = check_case(cid, row, lambda s, cid=cid: by[s].get(cid, []), errs)
        except Exception as e:  # a malformed case must be rejected, never crash the validator
            errs.append(("V1", f"could not be checked: {type(e).__name__}: {e}"))
        res[cid] = errs
    if not partial:  # variety rules and duplicate modules need all cases
        sS = [i for cid, i in info.items() if i and i["k"] < 20]
        g = d = 0
        for cid, i in info.items():
            if not i or i["k"] >= 20 or res[cid]:
                continue
            cr = by["crates"][cid]
            items = [(x["crate_id"], x["weight"], x["value"]) for x in cr]
            cap = next(r for r in tables["cases"] if r["case_id"] == cid)["capacity"]
            g += greedy(items, cap) < knap([(w, v) for _, w, v in items], cap)
            _, dist, fw = route_info(i["V"], i["nbr"], i["pen"])
            d += any(fw[t] > dist[t] for t in i["tg"])
        if g < 5: res["global"].append(("V7", f"variety 1: greedy suboptimal in only {g} tier-S cases (need 5)"))
        if d < 5: res["global"].append(("V7", f"variety 2: shortest-looks-cheapest in only {d} tier-S cases (need 5)"))
        rs = [i["ratio"] for i in info.values() if i and 20 <= i["k"] <= 45]
        if len(rs) != 26 or not all(2.5 <= r <= 6.0 for r in rs) or sum(r < 3.5 for r in rs) < 5 \
                or sum(3.5 <= r <= 4.8 for r in rs) < 8 or sum(r > 4.8 for r in rs) < 5:
            res["global"].append(("V7", "variety 3: safety rules per switch (need all in 2.5..6.0; >=5 below 3.5, >=8 in 3.5..4.8, >=5 above 4.8)"))
        for mod, sheets in MODULES.items():
            seen = {}
            for cid in cids:
                sig = tuple(tuple(tuple(v for kk, v in r.items() if kk != "case_id") for r in by[sh].get(cid, [])) for sh in sheets)
                if len(by[sheets[0]].get(cid, [])) >= 8:
                    if sig in seen: res["global"].append(("V7", f"variety 4: module {mod} of {cid} equals that of {seen[sig]}"))
                    seen[sig] = cid
    return res


def report_lines(res, partial):
    lines, ok = [], True
    for cid, errs in res.items():
        if cid == "global":
            continue
        if errs:
            ok = False
            lines.append(f"{cid}: FAIL")
            lines += [f"    {c}: {m}" for c, m in errs]
        else:
            lines.append(f"{cid}: PASS")
    if res["global"]:
        ok = False
        lines.append("workbook-level rules: FAIL")
        lines += [f"    {c}: {m}" for c, m in res["global"]]
    elif not partial:
        lines.append("workbook-level rules (sheets, headers, 50 cases, variety rules): PASS")
    lines.append("OVERALL: " + ("PASS" if ok else "FAIL"))
    return lines, ok


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    partial = "--partial" in sys.argv
    lines, ok = report_lines(validate(args[0], partial), partial)
    print("\n".join(lines))
    sys.exit(0 if ok else 1)
