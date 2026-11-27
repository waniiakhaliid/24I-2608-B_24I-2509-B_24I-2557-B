"""Validation layer: returns a list of problems; never crashes on bad data."""
from config import BIG_TABLES

REQUIRED = ["crates", "locations", "roads", "windows", "incidents"]

def validate_case(case):
    problems = []
    for t in REQUIRED:
        if len(case[t]) == 0:
            problems.append(f"{t}: no rows")
    for t in BIG_TABLES:
        if t in case and len(case[t]) and (case[t]["case_id"] != case["case_id"]).any():
            problems.append(f"{t}: foreign case_id rows")
    # TODO after we see headers: connected map from HQ (location 0),
    # weights are positive integers, W <= total weight, window start < finish.
    return problems