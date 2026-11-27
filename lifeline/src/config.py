from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
CACHE = RESULTS / "sample_data"      # per-table CSVs for the sample only
SAMPLE_CSV = RESULTS / "sample_cases.csv"
RESULTS_CSV = RESULTS / "results.csv"

DATASET_VERSION = "master_release_v1"
SEED = 84                             # group seed; also the sample rule
N_PER_TIER = {"S": 10, "M": 5, "L": 3, "X": 4}
TRAP_CASE_NOS = {46, 47, 48, 49}
RANDOM_SEED = 84                      # for any random graphs we generate

TABLES = ["cases", "crates", "locations", "roads", "waves", "windows",
          "incidents", "radio_log", "radio_patterns", "radio_reports", "claims"]
BIG_TABLES = TABLES[1:]               # everything except cases