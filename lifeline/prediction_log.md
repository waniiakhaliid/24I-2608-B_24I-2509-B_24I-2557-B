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
- **Commit before run:** 
- commit f5e1d6b6f25ea7be3edc24c39a94e3f482797dbd (HEAD -> main)
-  Module B: updated prediction log
- Author: waniiakhaliid <waniiakhaliidwork.gmail.com>
- Date:   Fri Nov 27 15:37:48 2026 +0500

    
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
- **After the run:**
  - **Measured vs predicted:**
    | # | Prediction | Measured | Verdict |
    |---|---|---|---|
    | 1 | Dijkstra time slope 1.1 +/- 0.25 | 1.112 +/- 0.092 (95% CI), R2 0.9980 | Held |
    | 2 | Bellman-Ford time slope 1.4 +/- 0.35 | 1.228 +/- 0.164, R2 0.9948 | Held, below my guess |
    | 3 | Dijkstra at V=4000 about 10 ms (x/÷ 3) | 26.6 ms | Inside tolerance, high end |
    | 4 | Bellman-Ford / Dijkstra time ratio at V=4000 about 4 (x/÷ 3) | 1.29 | Missed |
    | 5 | Bellman-Ford passes at V=4000 about 15 (x/÷ 2) | 8 | Held, low end |
    | 6 | Trap 4-48: fewest-roads route about 3x the cheapest (1.5 to 6) | Day 1: 187 / 59 = 3.17 | Held |
    | 7 | Day-1 destination reachable on all 22 sample cases | Yes (test passes) | Held |
    | 8 | Dijkstra and Bellman-Ford agree on cost everywhere | 0 disagreements on 154 case-days and 5 random sizes | Held |
  - **What I got wrong and why:**
    - Bellman-Ford needed only 5 to 8 passes, because shortest-path trees on these
      random graphs are shallow and the early exit stops the passes early. Its
      relaxations grew from 7,490 to 191,984 (about 26x for 16x the size), so it
      behaved near-linearly in practice despite the O(VE) worst case.
    - Dijkstra did 5.4x fewer operations than Bellman-Ford at V=4000 (35,772 vs
      191,984) but was only 1.29x faster in time. Each heap operation is several
      Python statements, while Bellman-Ford's inner loop is a single comparison.
      At V=1000 Bellman-Ford was faster (5.56 ms vs 6.23 ms), and the order also
      flipped at V=250 and V=500. The operation counts favour Dijkstra clearly; the
      wall clock barely does.
    - Absolute time was underestimated: about 1.1 us per edge examined against my
      0.5 us.
  - **Theory vs measurement clash:** Operation counts say Dijkstra wins by 5.4x;
    measured time says 1.29x, and it loses at some sizes. The cause is the constant
    factor of the Python heap (hypothesis, not separately tested). Also, the
    extrapolation error from four sizes to V=4000 was 4.3% (Dijkstra), 5.8%
    (Bellman-Ford) and 26.0% (BFS). BFS times are very small (0.13 to 4.2 ms), so
    timing noise is the likely cause (hypothesis).
  - **Trap and reachability observations:**
    - On 4-48 the fewest-roads route costs 3.17x the cheapest on days 1 and 7 and
      3.37x on day 4. On days 2, 3 and 5 (storm, closures) the ratio is only about
      1.1x, so this trap bites mainly on days with no minute multiplier or closure.
    - Case 2-01 on day 1 shows a ratio of 20, larger than the designated trap case.
    - The target is unreachable in 46 of 154 case-days (day 2: 4, day 3: 8, day 4: 5,
      day 5: 5, day 6: 13, day 7: 11). On 4-48, day 6 is unreachable. The campaign
      must therefore check reachability every day and skip the trip when it fails.
### Entry 3: Module C (rescue scheduling) earliest-finish greedy and weighted-interval DP vs greedy by value, scaling with n
- commit 2d37ed9a883be3757855d344fa91f24edb72cf01 (HEAD -> main)
- updated prediction log for module C, moved validator generator into data\phase1
- Author: eshallll <i242509@isb.nu.edu.pk>
- Date:   Sat Nov 28 07:36:50 2026 +0500

   
- **Experiment:** Windows from the sampled cases joined in sample order (pooling,
  Section 4.3: window times shifted by 1440 minutes per case, ids renumbered), first
  n = 200, 400, 800, 1600, 3200. Touching windows are compatible (finish <= next
  start). Primary: earliest-finish greedy (maximise count) and weighted-interval DP
  with binary search (maximise value). Baseline: greedy by value (highest value
  first, skip any window that overlaps one already chosen). Time: 1 warm-up, median
  of 5, IQR. Operation counts: key comparisons and element moves for the sort, binary
  search steps and table cells for the DP, windows examined for the greedy passes;
  sorting counted separately from the selection pass. Also run every sample case
  (count and value for each algorithm), and the 10 tier S cases against the
  `window_count_opt` and `window_value_opt` claims.
- **Expected winner:**
  - Speed: greedy by value and earliest-finish greedy are about equal; the DP is
    slowest by a small constant factor.
  - Quality: the DP wins on value and earliest-finish wins on count. Greedy by value
    should lose on both.
- **Numerical prediction (with tolerance):**
  1. Time slope vs n for all three algorithms: 1.1 (tolerance +/- 0.25), since each is
     O(n log n) and dominated by the sort.
  2. Weighted DP at n = 3200: about 15 ms, tolerance x/÷ 3. Earliest-finish greedy at
     n = 3200: about 5 ms, tolerance x/÷ 3.
  3. DP / earliest-finish time ratio at n = 3200: about 3, tolerance x/÷ 2.5.
  4. Greedy by value reaches about 80% of the DP's total value on the pooled inputs,
     tolerance +/- 15 points.
  5. Greedy by value schedules about 70% as many windows as earliest-finish,
     tolerance +/- 20 points.
  6. Earliest-finish count equals `window_count_opt`, and DP value equals
     `window_value_opt`, on all 10 tier S cases (no tolerance).
  7. The DP's value is at least as high as that of any other algorithm on every input,
     and earliest-finish's count is at least as high as any other's (no tolerance).
- **Reasoning:** All three algorithms sort once and then make one pass, so growth should
  be close to n log n, a slope slightly above 1. The DP adds a binary search per
  window, which costs a few times more than a plain pass, hence the 3x guess. Pooled
  inputs are independent blocks (each case sits in its own 1440-minute slot), so
  they should behave like many copies of a single case; quality ratios should not
  drift with n. The 80% and 70% figures are my least certain numbers: I have not
  looked at how heavily the sample windows overlap, only that tier L cases have about
  1,000 to 2,500 windows in a 1440-minute day. The absolute times assume about 1 to
  2 microseconds per window in pure Python.

- **After the run:**
  - **Measured vs predicted:**
    | # | Prediction | Measured | Verdict |
    |---|---|---|---|
    | 1 | Time slope 1.1 +/- 0.25 for all three algorithms | EF-greedy 1.203 +/- 0.141 (R2 0.9960); Weighted-DP 1.019 +/- 0.381 (R2 0.9602); Value-greedy 0.776 +/- 0.330 (R2 0.9491) | Held for EF and DP; missed for Value-greedy (0.776 is below 0.85) |
    | 2a | Weighted-DP at n=3200 about 15 ms (x/÷ 3) | 20.7 ms | Held |
    | 2b | EF-greedy at n=3200 about 5 ms (x/÷ 3) | 20.9 ms | Missed (limit was 15 ms) |
    | 3 | DP / EF time ratio at n=3200 about 3 (x/÷ 2.5) | 0.99 | Missed |
    | 4 | Value-greedy value about 80% of DP (+/- 15 points) | 82.7% at n=3200 (97.6% at n=200, falling to 82.7%) | Held at n=3200; the ratio drifts with n |
    | 5 | Value-greedy count about 70% of EF (+/- 20 points) | 75.0% at n=3200 (94.5% at n=200) | Held at n=3200; the ratio drifts with n |
    | 6 | EF count = window_count_opt and DP value = window_value_opt on all 10 tier S cases | test_tier_s_against_claims passes | Held |
    | 7 | DP value and EF count never beaten on any input | Held on all 22 quality rows and all five pooled sizes (asserted in the script) | Held |
  - **What I got wrong and why:**
    - EF-greedy and Weighted-DP took almost the same time (ratio 0.99), not 3x. The
      merge sort dominates both: it is the same sort, and the extra work in the DP
      (a binary search per window) is small next to it. In operations the DP costs
      1.44x as much as EF at n=3200 (107,015 vs 74,274), but the time hides that.
    - The absolute times were underestimated: about 6.5 us per window for EF-greedy
      (20.9 ms / 3200) against my 1 to 2 us. The own merge sort in pure Python is the
      likely reason (hypothesis).
    - Value-greedy's slope (0.776) is below 1 with a wide CI. The times are small
      (2.5 ms to 17 ms), and its time at n=3200 (17.1 ms) was below EF-greedy's, so
      timing noise is the likely cause (hypothesis).
    - I expected the quality ratios not to drift with n, because pooled blocks are
      independent. They did drift (value ratio 0.976, 0.954, 0.885, 0.844, 0.827).
      The pool joins cases in sample order, so the first 200 windows come from small
      tier S cases, and larger, denser cases enter as n grows. The per-case rows
      agree (below). This is a hypothesis; I did not test pools in a different order.
  - **Per-case quality (Value-greedy / DP value):** tier S is 1.000 on 8 of 10 cases
    (1-00 is 0.881, 3-09 is 0.756). Tier M ranges 0.581 to 0.920. Tier L ranges
    0.513 to 0.678. Trap cases: 1-46 0.568, 2-49 0.627, 7-47 0.520, and 4-48 is 0.210
    (count ratio 0.107), the worst case in the sample. Value-greedy is therefore worse
    than the DP on at least one case (test_value_greedy_loses_somewhere passes).
  - **Pooling check:** test_pooled_equals_sum_of_cases passes, so the pooled optima
    equal the sum of the per-case optima and no sampled case has windows past minute
    1440.
  - **Theory vs measurement clash:** Operation counts put the DP at 1.44x EF, and
    Value-greedy at 1.45x EF at n=3200 (107,393 vs 74,274), but measured times are
    nearly equal for the DP and EF, and Value-greedy is faster than EF at n=3200.
    The clash comes from constant factors and noise, not from a different growth
    order; the slope CIs for DP (+/- 0.381) and Value-greedy (+/- 0.330) are too wide
    to separate the algorithms.

### Entry 4: Module D (emergency queue) binary heap vs linear scan (and bucket queue), scaling with m
- **Date and time written:** 2026-11-28 HH:MM  (fill in the real time)
- **Commit before run:** (fill in the hash after committing this entry)
- **Experiment:** Alarms from the sampled cases joined in sample order (pooling,
  Section 4.3: ticks shifted past the previous case, ids renumbered), first
  m = 500, 1000, 2000, 4000, 8000. One alarm is released per tick, in urgency order
  (priority descending, then tick ascending, then alarm_id ascending) among alarms
  that have arrived. Primary: binary heap on (-priority, tick, alarm_id), written
  from scratch. Baseline: linear scan of the pending list. Extra series: 10-level
  FIFO bucket queue. Time: 1 warm-up, median of 5, IQR. Operation counts: key
  comparisons and element moves for the heap (a swap counts as 2), comparisons and
  element shifts for the scan, bucket appends and pops for the bucket queue. Also
  run every sample case and the campaign days with the extra alarm (priority 9 on
  day 2, priority 10 on day 5, both at tick 0), and compare the release orders.
- **Expected winner:** Bucket queue or heap on speed, with the linear scan clearly
  slowest at large m. All three must produce the same release order.
- **Numerical prediction (with tolerance):**
  1. Heap time slope vs m: 1.15 (tolerance +/- 0.25), since the cost is O(m log m).
  2. Linear-scan time slope vs m: 1.7 (tolerance +/- 0.35). The backlog grows
     linearly within a case, so the scan is quadratic, but the pool is made of
     separate cases, so the pooled slope should sit below 2.
  3. Bucket-queue time slope vs m: 1.0 (tolerance +/- 0.2).
  4. Heap at m = 8000: about 80 ms, tolerance x/÷ 3. Linear scan at m = 8000: about
     1.5 s, tolerance x/÷ 3.
  5. Linear scan / heap time ratio at m = 8000: about 20, tolerance x/÷ 3.
  6. Heap / bucket-queue time ratio at m = 8000: about 3, tolerance x/÷ 2.5. The
     bucket queue wins because there are only 10 priorities.
  7. The linear scan's comparisons at m = 8000 are about 3 million, tolerance
     x/÷ 2 (backlog about m^2/6 per case, summed over the pooled cases).
  8. All three algorithms release alarms in the identical order on every input, and
     no alarm is released before its arrival tick (no tolerance).
- **Reasoning:** The sample summary shows 1.29 to 1.74 alarms per tick on tiers M, L
  and X against one release per tick, so a backlog builds and drains within each
  case. The scan costs the backlog size per release, which gives roughly m^2/6 per
  case, while the heap pays about log2(backlog) per alarm. Pooling joins independent
  cases, so the scan's growth should be less than quadratic. I have not looked at
  the number of distinct priorities in the data; the proposal assumed 10. The
  absolute times assume about 0.5 microseconds per elementary step in Python, as
  in Modules B and C, and I am least sure of the 20x ratio.
- **After the run:**
  - Measured:
  - What I got wrong and why:
  - Theory vs measurement clash (if any):