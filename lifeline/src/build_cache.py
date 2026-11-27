"""Scan each big CSV once and keep only the sampled cases."""
import pandas as pd
from config import DATA, CACHE, SAMPLE_CSV, BIG_TABLES

def main():
    ids = set(pd.read_csv(SAMPLE_CSV)["case_id"])
    CACHE.mkdir(parents=True, exist_ok=True)
    for t in BIG_TABLES:
        path = DATA / f"{t}.csv"
        if not path.exists():
            print(f"skip {t} (no file)"); continue
        parts = [c[c["case_id"].isin(ids)]
                 for c in pd.read_csv(path, chunksize=500_000)]
        df = pd.concat(parts, ignore_index=True)
        df.to_csv(CACHE / f"{t}.csv", index=False)
        print(f"{t}: {len(df)} rows")

if __name__ == "__main__":
    main()