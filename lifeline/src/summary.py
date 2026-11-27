"""Summary table of sizes for the sampled cases (reads the cache)."""
import pandas as pd
from config import CACHE, SAMPLE_CSV, RESULTS

OUT = RESULTS / "sample_summary.csv"

def main():
    s = pd.read_csv(SAMPLE_CSV)
    out = s[["case_id", "case_no", "tier", "scenario", "capacity"]].copy()
    r = lambda t: pd.read_csv(CACHE / f"{t}.csv")
    cr, lo, ro, wa, wi, inc = (r(t) for t in
        ["crates", "locations", "roads", "waves", "windows", "incidents"])
    cid = out["case_id"]
    out["n_crates"] = cid.map(cr.groupby("case_id").size()).fillna(0).astype(int)
    out["total_w"] = cid.map(cr.groupby("case_id")["weight"].sum()).fillna(0).astype(int)
    out["V"] = cid.map(lo.groupby("case_id").size()).fillna(0).astype(int)
    out["E"] = cid.map(ro.groupby("case_id").size()).fillna(0).astype(int)
    out["n_waves"] = cid.map(wa.groupby("case_id")["wave_no"].nunique()).fillna(0).astype(int)
    out["n_windows"] = cid.map(wi.groupby("case_id").size()).fillna(0).astype(int)
    out["n_alarms"] = cid.map(inc.groupby("case_id").size()).fillna(0).astype(int)
    out["n_ticks"] = cid.map(inc.groupby("case_id")["tick"].nunique()).fillna(0).astype(int)
    out["alarms_per_tick"] = (out["n_alarms"] / (inc.groupby("case_id")["tick"].max()
        .reindex(cid).values + 1)).round(2)
    out["W_over_total"] = (out["capacity"] / out["total_w"]).round(2)
    out["W_over_14n"] = (out["capacity"] / (14 * out["n_crates"])).round(2)
    pd.set_option("display.width", 220)
    print(out.to_string(index=False))
    out.to_csv(OUT, index=False)

if __name__ == "__main__":
    main()