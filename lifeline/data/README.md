# LIFELINE master dataset, release v1 (2026-11-12)

This is the combined Iteration 1 data of all groups, for use in Iteration 2.
Cite it in your submission as **master_release_v1**.

- groups: 75
- cases: 3,622 (tier S 1,429, M 1,461, L 440, X 292)

Every case in this release passed the course staff's validation of the Phase 1 rules.
Cases that failed it were left out, so some groups contribute fewer than 50 cases
and case numbers within a group can have gaps.

## Files

- `<table>.csv`: one CSV per table (UTF-8, header row)
- `CHECKSUMS.txt`: SHA-256 of every file, to check your copy is complete

Several tables have more than 1,048,576 rows, so **do not open the large CSVs in Excel**: it silently cuts them off.

## Format

The tables and columns are exactly those of the Phase 1 workbook (Section 3 of the project
statement), with two columns added at the end of every table:

- `group_no`: the group whose generator produced the case
- `orig_case_id`: the case_id as that group wrote it

`case_id` is `<group_no>-<kk>` (for example `16-07`) and is unique across the whole dataset.
It joins the tables, as in the original workbook. `case_no`, `tier` and `scenario` in
`cases` are unchanged.

## Tables

| Table | Rows | Content |
|---|---:|---|
| `cases` | 3,622 | one row per case: tier, scenario, capacity, targets and the parameters of each module |
| `crates` | 859,467 | relief crates (module A): category, weight, value, expiry, serial |
| `locations` | 979,481 | network locations (module B): type D/S/H/J and penalty; location 0 is the HQ |
| `roads` | 1,343,950 | roads between locations: minutes and cable cost |
| `waves` | 403,563 | road closures, one row per closed road, grouped in waves |
| `radio_log` | 14,387 | radio log text, split into parts; join the text in part order |
| `radio_patterns` | 21,732 | six search patterns per case and their occurrence counts |
| `radio_reports` | 3,801 | pairs of reports to compare (edit distance) |
| `windows` | 1,535,262 | rescue windows (module C): start, finish, value |
| `incidents` | 3,193,832 | alarms (module D): arrival tick and priority |
| `sites` | 258,647 | relief site coordinates (modules H/I) |
| `tour` | 258,647 | planted closed tour through all sites |
| `pipeline_dims` | 197,912 | matrix-chain dimensions (module G) |
| `drum_prices` | 973,401 | price of a drum piece of each length (module G) |
| `sensor_edges` | 367,075 | sensor graph edges (module H) |
| `sensor_cover` | 61,554 | planted vertex cover of the sensor graph |
| `safety_rules` | 365,978 | 3-literal safety rules (module H) |
| `safety_planted` | 88,854 | planted satisfying switch assignment |
| `rations` | 118,925 | ration quantities and the planted subset that hits rations_target |
| `claims` | 1,429 | tier S only: exhaustive-search optima for checking your algorithms |

## Loading it

Python with pandas (CSV):
```python
import pandas as pd
crates = pd.read_csv('crates.csv')
one_case = crates[crates.case_id == '16-07']
```

Report problems with the dataset to the course TAs, quoting the release version and the case_id.