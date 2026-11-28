# LIFELINE: Phase 2 (Algorithmic Relief-Command Engine)

Group seed: 84 | Course: DAA, FAST-NUCES Islamabad | Dataset: master_release_v1

## Team
| Member | Roll no. | Modules |
|---|---|---|
| Wania Khalid | 24i2608 | A (relief inventory), B (route planning) |
| Eshaal Hussain | 24i2509 | C (rescue scheduling), D (emergency queue) |
| Hasnain Afkar | 24i2557 | E (radio logs), F (network planning) |

Status: modules A, B, C and D are implemented, tested and measured.
E, F and the 7-day campaign are TODO.

## Data
- Dataset: **master_release_v1** (released 2026-11-12), 75 groups, 3,622 cases.
- Checksums verified against `data/CHECKSUMS.txt` (SHA-256): all 19 files OK.
- The CSVs are not committed (too large). Place the release files in `data/`
  and run `uv run python src/verify_checksums.py`.
- Sample rule: per tier, cases at positions 84 mod 7 = 0, 7, 14, ... in master
  order, first N per tier, with N = {S: 10, M: 5, L: 3, X: 4} (our choice; the
  statement does not fix N). 22 cases, including tier L and all four traps
  (46 to 49). Listed in `results/sample_cases.csv`.
- The sample follows the seed rule and so comes from groups 1 to 7 only; our own
  84-xx cases are not in it.
- Sizes of the sample are in `results/sample_summary.csv`.
- Defective cases found: TODO (list case_ids, or "none").

## Hardware and software
- OS: Windows 11 (10.0.26200)
- CPU: Intel64 Family 6 Model 142 Stepping 12 (GenuineIntel)
- RAM: 16 GB
- Python 3.14.6 (MSC v.1944, 64 bit), managed with uv; pytest 9.2.0
- Timing: `time.perf_counter`, one discarded warm-up run, then median of 5 runs
  with interquartile range, single-threaded, data loading excluded. Memory:
  peak `tracemalloc` allocation of one extra run.
- Growth fits: least squares on log-log, slope with 95% confidence interval
  (Student t, 5 sizes), R2, and the error of predicting the largest size from a
  fit on the first four (`src/stats.py`).

## Setup
- Install: `uv sync` (Python version in `.python-version`)
- Dependencies: pandas (file reading), pytest (tests). No library is used
  inside any algorithm (own binary heaps and own merge sort).
- All commands below are run from the `lifeline/` folder.

## Run: data steps (once)
```
uv run python src/verify_checksums.py     # check the master dataset
uv run python src/sample.py               # pick the seed-84 sample
uv run python src/build_cache.py          # cache the sample's rows in results/sample_data/
uv run python src/summary.py              # size table of the sample
```

## Run: modules (tests and experiments)

Each module has its own test command and experiment command. The experiment
writes `results/results_<module>.csv` (columns as in the statement: module,
experiment, algorithm, instance, size, size2, time_s, time_iqr_s, ops,
mem_bytes, status, note) and `results/fit_<module>.txt`. A rerun replaces that
module's file only.

| Module | Algorithm file | Tests | Experiment script | Outputs |
|---|---|---|---|---|
| A relief inventory | `src/modules/knapsack.py` | `tests/test_knapsack.py`, `tests/test_fault_injection_A.py` | `src/experiments/exp_knapsack.py` | `results_A.csv`, `fit_A.txt` |
| B route planning | `src/modules/routing.py`, `src/graphgen.py` | `tests/test_routing.py`, `tests/test_fault_injection_B.py` | `src/experiments/exp_routing.py` | `results_B.csv`, `fit_B.txt` |
| C rescue scheduling | `src/modules/scheduling.py` | `tests/test_scheduling.py`, `tests/test_fault_injection_C.py` | `src/experiments/exp_scheduling.py` | `results_C.csv`, `fit_C.txt` |
| D emergency queue | `src/modules/alarm_queue.py` | `tests/test_alarm_queue.py`, `tests/test_fault_injection_D.py` | `src/experiments/exp_alarm_queue.py` | `results_D.csv`, `fit_D.txt` |

Shared by all modules: `src/config.py`, `src/loader.py`, `src/validation.py`,
`src/harness.py` (timing and results files), `src/stats.py` (growth fit),
`tests/reference.py` (brute-force and plain-definition references, kept out of
`src/`), `tests/conftest.py`. Module D imports the merge sort from
`modules/scheduling.py`.

### Module A: relief inventory (knapsack)
```
uv run pytest tests/test_knapsack.py tests/test_fault_injection_A.py -v
uv run python src/experiments/exp_knapsack.py
```

### Module B: route planning
```
uv run pytest tests/test_routing.py tests/test_fault_injection_B.py -v
uv run python src/experiments/exp_routing.py
```

### Module C: rescue scheduling
```
uv run pytest tests/test_scheduling.py tests/test_fault_injection_C.py -v
uv run python src/experiments/exp_scheduling.py
```

### Module D: emergency queue
```
uv run pytest tests/test_alarm_queue.py tests/test_fault_injection_D.py -v
uv run python src/experiments/exp_alarm_queue.py
```

### Everything
```
uv run pytest tests -v                            # all tests
uv run python src/combine_results.py              # merge results_<module>.csv into results/results.csv
```
- 7-day campaign: TODO

Random seeds: group seed 84 (sample rule, random tests use `random.Random(84)`,
random maps for the Module B scaling use seed 84 + V).

## Problem definitions
- **A. Relief inventory:** 0/1 knapsack. Primary: DP over capacity with
  traceback. Baseline: ratio greedy (exact cross-multiplication). Reference
  (tests only): brute force, n <= 20.
- **B. Route planning:** cheapest routes, reachability and fewest-roads route.
  Primary: heap Dijkstra (cost) and BFS (reachability, fewest roads).
  Baseline: Bellman-Ford. Reference (tests only): all simple paths, n <= 8.
- **C. Rescue scheduling:** interval scheduling, touching windows compatible.
  Primary: earliest-finish greedy (count) and weighted-interval DP (value).
  Baseline: greedy by value. Reference (tests only): all compatible subsets,
  n <= 14.
- **D. Emergency queue:** one alarm released per tick in urgency order.
  Primary: binary heap. Baseline: linear scan of the pending list. Extra
  series: 10-level bucket queue. Reference (tests only): the plain definition
  (minimum over the arrived alarms at each tick).
- **E. Radio logs:** pattern matching, edit distance, prefix code (TODO).
- **F. Network planning:** minimum spanning tree (TODO).

## Conventions and tie rules (Section 4.4)
- Every ordering is total; ties are broken by id ascending.
- A: crate ratio value/weight compared by cross-multiplication; DP takes a crate
  only if it strictly improves the value.
- B: a directed step u to v costs minutes + penalty of v; every road gives two
  steps. Dijkstra heap key (cost, node id); BFS visits neighbours in ascending id.
- C: windows sorted by (finish, window_id); value-greedy by (value descending,
  window_id); the DP takes a window only if it strictly improves the value.
- D: urgency = priority descending, then tick ascending, then alarm_id ascending.
  If nothing is waiting, time jumps to the next arrival tick.
- Campaign calendar (Section 7.4) as implemented so far: wave i means wave
  (i mod number of waves); days 6 and 7 close the union of all waves (not every
  road); storm multiplies minutes by 1.5 rounded up; dangerous area doubles
  penalties of 2 or more; windows with (window_id + day) divisible by 5 are
  unavailable; day 2 adds a priority-9 alarm and day 5 a priority-10 alarm at
  tick 0 (new alarm_id = max id + 1).
- Pooling (Section 4.3): crates appended; windows shifted by 1440 minutes per
  case; alarm ticks shifted past the previous case; ids renumbered. Networks are
  never pooled: Module B scaling uses random connected maps (random spanning tree
  plus extra roads, E about 3V, minutes 1 to 60, penalties from {0, 1, 2, 4, 6}).

## Operation counts (definitions)
Preprocessing is counted separately where it exists (field `sort` vs `select`
in the `note` column).
- **A, DP over capacity (selection and tabulation):** table cells computed, i.e.
  the sum over crates that fit of (W - weight + 1).
- **A, ratio greedy (ordering):** key comparisons made while sorting plus crates
  examined in the fill pass.
- **B, heap Dijkstra (map exploration):** edges examined + heap pushes + heap
  pops (heap key comparisons are reported in `note` as `heap_cmp`).
- **B, Bellman-Ford:** relaxations attempted (passes reported in `note`).
- **B, BFS:** nodes visited + edges examined.
- **C, sort (own merge sort):** key comparisons + element placements.
- **C, earliest-finish greedy:** windows examined in the selection pass.
- **C, weighted DP:** table cells computed + binary-search steps.
- **C, value-greedy:** windows examined + binary-search steps + element shifts.
- **D, sort of arrivals:** key comparisons + element placements (merge sort).
- **D, binary heap:** key comparisons + element moves (a swap counts as 2).
- **D, linear scan:** key comparisons + element shifts when an alarm leaves the
  pending list.
- **D, bucket queue:** appends + pops + priority-level checks.
- E, F: TODO.

## Testing
- Verification code is in `tests/reference.py`, separate from `src/`.
- Each module has unit, boundary, malformed-input, random-versus-reference,
  sample-case (all 7 days where the module is calendar-driven) and trap tests,
  plus fault-injection tests: a broken copy of the algorithm must fail the
  reference check (wrong boundary, wrong tie rule or sort key, wrong direction,
  ignored closures, missing validation).
- Tier S claims: A matches `cargo_opt` and C matches `window_count_opt` and
  `window_value_opt` on all 10 tier S cases.
- Test counts: A 15, B 15, C 20, D 21 (expected total 71; confirm with
  `uv run pytest tests -v`).
- Failures found and fixed during development are documented in the report
  (a test that misread the closure rule for days 6 and 7; stray imports after
  the file reorganisation; the reference file not updated for a new module).

## Prediction log
`prediction_log.md` has one entry per experiment round: Entry 1 (A), Entry 2
(B), Entry 3 (C), Entry 4 (D). Each entry was committed before its experiment
was run; the "After the run" parts record predictions that were missed.

## Proposal choices kept or changed
- A: kept (DP primary, ratio greedy baseline). Brute force is used only as a
  test reference, not as an experiment baseline.
- B to D: kept as proposed. Added the bucket queue as an extra series in D.
- TODO: E and F, and anything changed after the experiments, with reasons.

## Recommendation to the lead designer (Problem N)
TODO: per module: algorithm to ship, evidence (cite the experiment), the
assumption it depends on, and one condition under which it would be wrong, with
the measurement that would show it. End with the top 3 failure risks.

## Limitations
- Timing noise on the test machine is large (IQR up to about 30% of the median
  at some sizes), which widens the slope confidence intervals.
- Sample comes from groups 1 to 7 only (seed rule).
- TODO: complete after the other modules and the campaign.

## Files
```
README.md, prediction_log.md, repository.txt, report.pdf (TODO)
data/        master_release_v1 (CSVs not committed), CHECKSUMS.txt, Phase 1 files
proposal/    proposal.pdf, approach.pdf
src/         config, loader, validation, harness, stats, graphgen, sample, summary,
             build_cache, verify_checksums, combine_results
src/modules/ knapsack.py, routing.py, scheduling.py, alarm_queue.py
src/experiments/ exp_knapsack.py, exp_routing.py, exp_scheduling.py, exp_alarm_queue.py
tests/       reference.py, conftest.py, test_<module> and test_fault_injection_<A..D>
results/     sample_cases.csv, sample_summary.csv, results_<A..D>.csv, fit_<A..D>.txt,
             pytest_output.txt, screenshots/
```