"""Module: sites + planted tour."""
import itertools


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def gen_sites(rng, n):
    seen, pts = set(), []
    while len(pts) < n:
        p = (rng.randint(0, 999), rng.randint(0, 999))
        if p not in seen:
            seen.add(p)
            pts.append(p)
    return pts


def closed_len(pts, tour):
    return sum(manhattan(pts[tour[i]], pts[tour[(i + 1) % len(tour)]]) for i in range(len(tour)))


def nn_tour(pts, high_tie=False):
    unv, t, cur = set(range(1, len(pts))), [0], 0
    while unv:
        cur = min(unv, key=lambda j: (manhattan(pts[cur], pts[j]), -j if high_tie else j))
        unv.remove(cur)
        t.append(cur)
    return t


def two_opt(pts, tour):
    n = len(tour)
    D = [[manhattan(a, b) for b in pts] for a in pts]
    improved = True
    while improved:
        improved = False
        for i in range(n - 2):
            a, b = tour[i], tour[i + 1]
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                c, d = tour[j], tour[(j + 1) % n]
                if D[a][c] + D[b][d] < D[a][b] + D[c][d]:
                    tour[i + 1:j + 1] = reversed(tour[i + 1:j + 1])
                    b = tour[i + 1]
                    improved = True
    return tour


def optimal_tour(pts):
    n = len(pts)
    D = [[manhattan(a, b) for b in pts] for a in pts]
    best, bt = None, None
    for perm in itertools.permutations(range(1, n)):
        if perm[0] > perm[-1]:
            continue
        L = D[0][perm[0]] + sum(D[perm[i]][perm[i + 1]] for i in range(n - 2)) + D[perm[-1]][0]
        if best is None or L < best:
            best, bt = L, perm
    return [0] + list(bt), best


def planted_tour(pts, tier):
    """S: exhaustive optimum. M/L/X: nearest-neighbour + 2-opt (never longer than either NN tie rule)."""
    if tier == "S":
        t, _ = optimal_tour(pts)
        return t
    cands = [two_opt(pts, nn_tour(pts, h)) for h in (False, True)]
    t = min(cands, key=lambda c: closed_len(pts, c))
    assert closed_len(pts, t) <= min(closed_len(pts, nn_tour(pts, h)) for h in (False, True))
    return t
