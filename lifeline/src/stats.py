"""Shared least-squares fit for all modules' growth claims."""
import math

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}


def loglog_fit(xs, ys):
    """Fit log(y) = icpt + slope * log(x). Returns (slope, 95% CI half-width, R2, icpt)."""
    lx, ly = [math.log(x) for x in xs], [math.log(y) for y in ys]
    n = len(xs)
    mx, my = sum(lx) / n, sum(ly) / n
    sxx = sum((a - mx) ** 2 for a in lx)
    slope = sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sxx
    icpt = my - slope * mx
    ss_res = sum((b - (icpt + slope * a)) ** 2 for a, b in zip(lx, ly))
    ss_tot = sum((b - my) ** 2 for b in ly)
    ci = T975[n - 2] * math.sqrt(ss_res / (n - 2) / sxx)
    return slope, ci, 1 - ss_res / ss_tot, icpt