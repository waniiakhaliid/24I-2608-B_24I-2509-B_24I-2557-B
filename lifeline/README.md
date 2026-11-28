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
- Checksums verified against `data/CHECKSUMS.txt` (SHA-256): all 19 files OK.
- The CSVs are not committed (too large). Place the release files in `data/`
  and run `python src/verify_checksums.py`.
- Sample rule: per tier, cases at positions 84 mod 7 = 0, 7, 14, ... in master
  order, first N per tier, with N = {S: 10, M: 5, L: 3, X: 4} (our choice; the
  statement does not fix N). 22 cases, including tier L and all four traps
  (46 to 49). Listed in `results/sample_cases.csv`.
- The sample follows the seed rule and so comes from groups 1 to 7 only; our own
  84-xx cases are not in it.
- Defective cases found: TODO (list case_ids, or "none").

## Hardware and software
- OS: Windows 11 (10.0.26200)
- CPU: Intel64 Family 6 Model 142 Stepping 12 (GenuineIntel)
- RAM: 16 GB
- Python 3.14.6 (MSC v.1944, 64 bit), managed with uv; pytest 9.2.0
- Timing: `time.perf_counter`, one discarded warm-up run, then median of 5 runs
  with interquartile range, single-threaded, data loading excluded. Memory:
  peak `tracemalloc` allocation of one extra run.

## Setup
- Install: `uv sync` (Python version in `.python-version`)
- Dependencies: pandas (file reading), pytest (tests). No library is used
  inside any algorithm.

## Run
- Verify data: `uv run python src/verify_checksums.py`
- Build sample: `uv run python src/sample.py`
- Build sample cache: `uv run python src/build_cache.py`
- Size summary: `uv run python src/summary.py`
- Run tests: `uv run pytest tests -v`
- Module A experiments: `uv run python src/exp_knapsack.py`
  (writes `results/results_A.csv` and `results/fit_A.txt`)
- Combine results into `results/results.csv`: `uv run python src/combine_results.py`
- Run 7-day campaign: TODO

Random seeds: group seed 84 (sample rule, random tests, any generated graphs).

## Operation counts (definitions)
- **A, DP over capacity (Selection and tabulation):** table cells computed,
  i.e. the sum over crates that fit of (W - weight + 1).
- **A, ratio greedy:** key comparisons made while sorting, plus crates examined
  in the fill pass.
- B to F: TODO (define when each module is added).

## Problem definitions
- A. Relief inventory: 0/1 knapsack (primary: DP over capacity with traceback;
  baseline: ratio greedy; reference: brute force in `tests/reference.py`)
- B. Route planning: shortest paths + reachability (primary: heap Dijkstra + BFS; baseline: Bellman-Ford)
- C. Rescue scheduling: interval scheduling (primary: earliest-finish greedy, weighted-interval DP; baseline: greedy by value)
- D. Emergency queue: priority queue (primary: binary heap; baseline: linear scan)
- E. Radio logs: pattern matching, edit distance, prefix code (primary: KMP, DP, Huffman; baselines: naive, memoised recursion, fixed-length)
- F. Network planning: MST (primary: Kruskal; baseline: Prim with heap)

## Testing
- Module A: 15 tests (unit, boundary, malformed input, random comparison with
  brute force, tier S claims check on 10 cases, medium-case invariants, trap
  7-47, 4 fault-injection tests). Verification code is in `tests/reference.py`,
  separate from `src/`.

## Proposal choices kept or changed
- A: kept (DP primary, ratio greedy baseline). Brute force is used only as a
  test reference, not as an experiment baseline. TODO: B to F.

## Recommendation to the lead designer (Problem N)
TODO: per module: algorithm to ship, evidence, assumption, one condition
under which it would be wrong. End with the top 3 failure risks.

## Limitations
- Timing noise on the test machine is large (IQR up to about 30% of the median
  at some sizes), which widens the slope confidence intervals.
- TODO: complete after the other modules.

## Files
prediction_log.md, report.pdf, repository.txt, data/ (master_release_v1 + data/phase1/),
proposal/ (proposal.pdf), docs/ (Phase 1 report and notes), src/, tests/, results/# LIFELINE: Phase 2 (Algorithmic Relief-Command Engine)

Group seed: 84 | Course: DAA, FAST-NUCES Islamabad

## Team
| Member | Roll no. | Modules |
|---|---|---|
| Wania Khalid | 24i2608 | A (relief inventory), B (route planning) |
| Eshaal Hussain | 24i2509 | C (rescue scheduling), D (emergency queue) |
| Hasnain Afkar | 24i2557 | E (radio logs), F (network planning) |

## Data
- Dataset: **master_release_v1** (released 2026-11-12), 75 groups, 3,622 cases.
- Checksums verified against `data/CHECKSUMS.txt` (SHA-256): all 19 files OK.
- The CSVs are not committed (too large). Place the release files in `data/`
  and run `python src/verify_checksums.py`.
- Sample rule: per tier, cases at positions 84 mod 7 = 0, 7, 14, ... in master
  order, first N per tier, with N = {S: 10, M: 5, L: 3, X: 4} (our choice; the
  statement does not fix N). 22 cases, including tier L and all four traps
  (46 to 49). Listed in `results/sample_cases.csv`.
- The sample follows the seed rule and so comes from groups 1 to 7 only; our own
  84-xx cases are not in it.
- Defective cases found: TODO (list case_ids, or "none").

## Hardware and software
- OS: Windows 11 (10.0.26200)
- CPU: Intel64 Family 6 Model 142 Stepping 12 (GenuineIntel)
- RAM: TODO
- Python 3.14.6 (MSC v.1944, 64 bit), managed with uv; pytest 9.2.0
- Timing: `time.perf_counter`, one discarded warm-up run, then median of 5 runs
  with interquartile range, single-threaded, data loading excluded. Memory:
  peak `tracemalloc` allocation of one extra run.

## Setup
- Install: `uv sync` (Python version in `.python-version`)
- Dependencies: pandas (file reading), pytest (tests). No library is used
  inside any algorithm.

## Run
- Verify data: `uv run python src/verify_checksums.py`
- Build sample: `uv run python src/sample.py`
- Build sample cache: `uv run python src/build_cache.py`
- Size summary: `uv run python src/summary.py`
- Run tests: `uv run pytest tests -v`
- Module A experiments: `uv run python src/exp_knapsack.py`
  (writes `results/results_A.csv` and `results/fit_A.txt`)
- Combine results into `results/results.csv`: `uv run python src/combine_results.py`
- Run 7-day campaign: TODO
- Module C: 
- uv run python -c "import pandas as pd; d=pd.read_csv('results/sample_data/windows.csv'); print((d.finish-d.start).min())"

Random seeds: group seed 84 (sample rule, random tests, any generated graphs).

## Operation counts (definitions)
- **A, DP over capacity (Selection and tabulation):** table cells computed,
  i.e. the sum over crates that fit of (W - weight + 1).
- **A, ratio greedy:** key comparisons made while sorting, plus crates examined
  in the fill pass.
- B to F: TODO (define when each module is added).

## Problem definitions
- A. Relief inventory: 0/1 knapsack (primary: DP over capacity with traceback;
  baseline: ratio greedy; reference: brute force in `tests/reference.py`)
- B. Route planning: shortest paths + reachability (primary: heap Dijkstra + BFS; baseline: Bellman-Ford)
- C. Rescue scheduling: interval scheduling (primary: earliest-finish greedy, weighted-interval DP; baseline: greedy by value)
- D. Emergency queue: priority queue (primary: binary heap; baseline: linear scan)
- E. Radio logs: pattern matching, edit distance, prefix code (primary: KMP, DP, Huffman; baselines: naive, memoised recursion, fixed-length)
- F. Network planning: MST (primary: Kruskal; baseline: Prim with heap)

## Testing
- Module A: 15 tests (unit, boundary, malformed input, random comparison with
  brute force, tier S claims check on 10 cases, medium-case invariants, trap
  7-47, 4 fault-injection tests). Verification code is in `tests/reference.py`,
  separate from `src/`.

## Proposal choices kept or changed
- A: kept (DP primary, ratio greedy baseline). Brute force is used only as a
  test reference, not as an experiment baseline. TODO: B to F.

## Recommendation to the lead designer (Problem N)
TODO: per module: algorithm to ship, evidence, assumption, one condition
under which it would be wrong. End with the top 3 failure risks.

## Limitations
- Timing noise on the test machine is large (IQR up to about 30% of the median
  at some sizes), which widens the slope confidence intervals.
- TODO: complete after the other modules.

## Files
prediction_log.md, report.pdf, repository.txt, data/ (master_release_v1 + data/phase1/),
proposal/ (proposal.pdf), docs/ (Phase 1 report and notes), src/, tests/, results/