# LIFELINE: Phase 2 (Algorithmic Relief-Command Engine)

Group seed: 84 | Course: DAA, FAST-NUCES Islamabad

## Team
| Member | Roll no. | Modules |
|---|---|---|
| Wania Khalid | 24i2608 | A (relief inventory), B (route planning) |
| Eshaal Hussain | 24i2509 | C (rescue scheduling), D (emergency queue) |
| Hasnain Afkar | 24i2557 | E (radio logs), F (network planning) |

## Data
- Dataset: **master_release_v1** (released 2026-11-12), 75 groups, 3,622 cases.
- Checksums verified against `data/CHECKSUMS.txt` (SHA-256): all files OK.
- The CSVs are not committed (too large). Place the release files in `data/`
  and run `python src/verify_checksums.py`.
- Sample: for each tier, cases at positions 84 mod 7 = 0, 7, 14, ... in master
  order, first N per tier. Listed in `results/sample_cases.csv`.
- Defective cases found: TODO (list case_ids, or "none").

## Setup
- Python: TODO (version from `.python-version`)
- Install: TODO (e.g. `uv sync`)

## Run
- Verify data: `python src/verify_checksums.py`
- Build sample: `python src/sample.py`
- Run tests: TODO
- Run experiments: TODO
- Run 7-day campaign: TODO

## Problem definitions
- A. Relief inventory: 0/1 knapsack (primary: DP; baseline: ratio greedy)
- B. Route planning: shortest paths + reachability (primary: heap Dijkstra + BFS; baseline: Bellman-Ford)
- C. Rescue scheduling: interval scheduling (primary: earliest-finish greedy, weighted-interval DP; baseline: greedy by value)
- D. Emergency queue: priority queue (primary: binary heap; baseline: linear scan)
- E. Radio logs: pattern matching, edit distance, prefix code (primary: KMP, DP, Huffman; baselines: naive, memoised recursion, fixed-length)
- F. Network planning: MST (primary: Kruskal; baseline: Prim with heap)

## Proposal choices kept or changed
TODO (fill in after experiments, with reasons).

## Recommendation to the lead designer (Problem N)
TODO: per module: algorithm to ship, evidence, assumption, one condition
under which it would be wrong. End with the top 3 failure risks.

## Limitations
TODO

## Files
prediction_log.md, report.pdf, repository.txt, data/, proposal/, src/