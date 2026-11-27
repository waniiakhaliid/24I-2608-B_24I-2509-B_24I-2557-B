import pandas as pd
from config import CACHE, BIG_TABLES
for t in BIG_TABLES:
    p = CACHE / f"{t}.csv"
    if p.exists():
        df = pd.read_csv(p, nrows=3)
        print(f"\n== {t} ==\n{df.to_string(index=False)}")