### Entry 1: Module A (relief inventory) DP vs ratio greedy, scaling with n
- **Date and time written:** 
   Fri Nov 27 10:02:49 2026 +0500
- **Commit before run:** 
-   commit fa207dc570253ceaa8966b7d77e008e021112cdb (HEAD -> main)
-  Author: waniiakhaliid <waniiakhaliidwork.gmail.com>
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
- **Commit after run:** 
-  commit 94aa1aff6d14c139adb61d534d986eef11778f91 (HEAD -> main)
-  add experiment_knapsack,separated bruteforce knapsack into test folder
-  Date:   Fri Nov 27 14:59:05 2026 +0500
-  Author: waniiakhaliid <waniiakhaliidwork.gmail.com>
  - **Measured vs predicted:**
    | Prediction | Measured | Verdict |
    |---|---|---|
    | DP time slope 2.0 +/- 0.2 | 2.132 +/- 0.209 (95% CI), R2 0.9972 | Held (CI contains 2.0) |
    | Greedy time slope 1.1 +/- 0.3 | 1.196 +/- 0.296, R2 0.9821 | Held |
    | DP at n=1600 about 2 s (x/÷ 3) | 1.020 s | Inside tolerance, low end |
    | Greedy at n=1600 under 5 ms | 6.35 ms | Missed |
    | DP/greedy time ratio at n=1600 about 500 (x/÷ 4) | about 161 | Inside tolerance, low end |
    | Greedy >= 95% of DP on ordinary cases | M and L: 99.6% to 100%; tier S: 2-01 61.8%, 3-02 92.2%, 1-00 94.98% | Held for M and L, wrong for tier S |
    | Trap 47: greedy about 55% of DP (+/- 10 points) | 7-47: 40 / 94 = 42.6% | Missed |
    | DP equals cargo_opt on all 10 tier S cases | DP equals cargo_opt on all 10 tier S cases | Held (test_tier_s_against_claims passes)|
  - **What I got wrong and why:**
    - Cost per cell was about 0.107 us (1.020 s / 9.52M cells), not the 0.2 us I
      assumed, so the absolute DP time was overestimated by about 2x. The slope was
      unaffected because it depends on the cell count, not the constant.
    - Greedy was slower than 5 ms because sorting with a Python comparison function
      costs more than I allowed for.
    - The 55% figure for trap 47 came from our own case 84-47. Case 7-47 comes from
      group 7's generator, and its trap is harsher (42.6%). This is a likely
      explanation, not a tested one.
    - "At least 95% on ordinary cases" was too broad. Tiny tier S instances leave
      greedy little room to fill the truck, so it can lose badly there. Traps 46, 48
      and 49 are not knapsack traps: greedy reached 99.9% or more on them.
  - **Cell count:** 9,522,166 at n=1600 is slightly below n x (W+1) = 9,540,000
    because the code counts W - wi + 1 cells per crate. This is not a clash.
  - **Theory vs measurement clash:** Predicting n=1600 from a fit on the first four
    sizes erred by 45.2% for DP (14.1% for greedy), although the slope CI is only
    +/- 0.2. The IQR reached about 30% of the median at n=800 (0.092 s on 0.301 s),
    so timing noise is the likely cause. This is a hypothesis; more repeats on a
    quieter machine would test it.

### Entry 2: Module B (route planning) heap Dijkstra vs Bellman-Ford, scaling with V
- **Date and time written:** 2026-11-27 HH:MM  (fill in the real time)
- **Commit before run:** (fill in the hash after committing this entry)
- **Experiment:** Single-source cheapest cost from the HQ (location 0) on random
  connected graphs built from seed 84 (random spanning tree plus extra roads,
  E = 3V, minutes 1 to 60, penalties from {0, 1, 2, 4, 6}), V = 250, 500, 1000,
  2000, 4000. Networks are not pooled. Primary: heap Dijkstra. Baseline:
  Bellman-Ford (stops early when a full pass changes nothing). BFS (fewest roads)
  is timed as an extra series. Also run on the 22 sample cases (cost, reachability)
  and on trap 4-48, comparing the cost of the fewest-roads route with the cheapest.
  Time: 1 warm-up, median of 5, IQR. Operation counts: relaxations attempted,
  edges examined, heap operations (Dijkstra); passes and relaxations (Bellman-Ford);
  nodes visited (BFS).
- **Expected winner:** Heap Dijkstra on speed. Both give the same cost, which is
  checked on every input.
- **Numerical prediction (with tolerance):**
  1. Dijkstra time slope vs V: 1.1 (tolerance +/- 0.25), since E = 3V and the cost is
     O((V+E) log V).
  2. Bellman-Ford time slope vs V: 1.4 (tolerance +/- 0.35). Worst case is O(VE),
     slope 2, but early exit should stop after about the depth of the shortest-path
     tree, which grows slowly on a random graph.
  3. Dijkstra at V = 4000 (E = 12,000): about 10 ms, tolerance x/÷ 3.
  4. Bellman-Ford / Dijkstra time ratio at V = 4000: about 4, tolerance x/÷ 3.
  5. Bellman-Ford passes at V = 4000: about 15, tolerance x/÷ 2.
  6. On trap 4-48, the fewest-roads route costs about 3 times the cheapest, tolerance
     between 1.5 and 6. Our own trap 84-48 gave 5.7 in the proposal; I expect group 4
     to differ.
  7. Day-1 destination is reachable on all 22 sample cases (no tolerance).
  8. Dijkstra and Bellman-Ford agree on cost on every input (no tolerance).
- **Reasoning:** The sample summary shows E is about 1.1 to 1.3 times V on real cases,
  so the maps are sparse and the heap pays off. Bellman-Ford only reaches its
  quadratic worst case if shortest paths are long chains, which a random spanning
  tree plus extra roads should avoid. The absolute times assume about 0.5 microseconds
  per edge in Python heap code; this is my least certain number. I expect the
  slopes to be better predicted than the times, as in Module A.
- **After the run:**
  - Measured:
  - What I got wrong and why:
  - Theory vs measurement clash (if any):
  