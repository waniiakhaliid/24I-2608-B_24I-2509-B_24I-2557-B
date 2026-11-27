### Entry 1: Module A (relief inventory) DP vs ratio greedy, scaling with n
- **Date and time written:** 2026-11-27 HH:MM  (fill in the real time)
- **Commit before run:** (fill in the hash after committing this entry)
- **Experiment:** 0/1 knapsack on pooled crate sets of n = 100, 200, 400, 800, 1600
  (consecutive sampled cases joined as in Section 4.3). Capacity per input is set
  to the same fraction of total weight as in the sample (about 0.3 to 0.4). Primary:
  DP over capacity with traceback. Baseline: ratio greedy. Time: 1 warm-up, median
  of 5, IQR. Operation count: DP table cells computed; greedy items examined.
  Also run on the trap cases to compare value.
- **Expected winner:**
  - Speed: ratio greedy.
  - Quality: DP (exact).
  - On trap case 47, DP should beat greedy by a large margin.
- **Numerical prediction (with tolerance):**
  1. DP cells = n x (W+1) exactly, so the ops column is deterministic. Since W
     grows with n (about 3.3n from the sample), cells grow like n^2.
     Log-log slope of DP time vs n: 2.0 (tolerance +/- 0.2).
  2. Greedy time slope vs n: 1.1 (tolerance +/- 0.3, because n log n and Python
     overhead blur it).
  3. DP at n = 1600 (W about 5,300, about 8.5M cells): about 2 s in pure Python,
     tolerance x/÷ 3. Greedy at n = 1600: under 5 ms.
  4. DP/greedy time ratio at n = 1600: about 500, tolerance x/÷ 4.
  5. Greedy value is at least 95% of the DP optimum on ordinary cases,
     and about 55% on trap 47 (the figure our proposal claimed), tolerance +/- 10 points.
  6. DP matches `cargo_opt` on all 10 tier S cases (exact, no tolerance).
- **Reasoning:** The DP cost is n x W, and the sample summary shows W is
  about 0.17 to 0.64 of total weight with weights 1 to 20, so W is proportional
  to n and the cost is quadratic. Greedy only sorts, so it is O(n log n).
  The absolute time guess assumes roughly 0.2 microseconds per cell in a pure
  Python loop; I am least sure of this number. Greedy gets close to the optimum
  when many small crates fill the truck, but trap 47 is built so that the best
  value-per-kg crate blocks the better combination.
- **After the run:**
  