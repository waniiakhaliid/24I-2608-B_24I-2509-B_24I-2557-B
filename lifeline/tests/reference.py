"""Trusted reference solvers for checking the submitted modules.
Kept in tests/ on purpose: verification code is separate from src/ (Section 7.2).
Deliberately simple and slow; only for small inputs."""


def knapsack_bruteforce(weights, values, capacity, max_n=20):
    """Exact 0/1 knapsack by trying all 2^n subsets. Returns (value, chosen)."""
    n = len(weights)
    if n > max_n:
        raise ValueError(f"brute force limited to n <= {max_n}, got {n}")
    best_v, best_mask = -1, 0
    for mask in range(1 << n):
        w = v = 0
        for i in range(n):
            if (mask >> i) & 1:
                w += weights[i]
                v += values[i]
        if w <= capacity and v > best_v:
            best_v, best_mask = v, mask
    return best_v, [i for i in range(n) if (best_mask >> i) & 1]