"""Data loader: returns plain per-case tables from the cached sample."""
import pandas as pd
from config import CACHE, SAMPLE_CSV, BIG_TABLES

_tables = {}

def _table(name):
    if name not in _tables:
        _tables[name] = pd.read_csv(CACHE / f"{name}.csv")
    return _tables[name]

def sample_cases():
    return pd.read_csv(SAMPLE_CSV)

def load_case(case_id):
    """Dict: 'meta' (one row as dict) plus one DataFrame per table."""
    meta = sample_cases().set_index("case_id").loc[case_id].to_dict()
    case = {"case_id": case_id, "meta": meta}
    for t in BIG_TABLES:
        df = _table(t)
        case[t] = df[df["case_id"] == case_id].reset_index(drop=True)
    return case