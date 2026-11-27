"""Random connected maps for scaling experiments (Section 4.3: networks are never pooled).
Random spanning tree + extra roads, minutes 1..60, penalties from {0,1,2,4,6}."""
import random

PENALTIES = [0, 1, 2, 4, 6]


def random_graph(V, seed, extra_factor=2):
    rng = random.Random(seed)
    penalties = [0] + [rng.choice(PENALTIES) for _ in range(V - 1)]
    roads = []
    for v in range(1, V):                       # spanning tree: v joins a random earlier node
        roads.append((len(roads), rng.randrange(v), v, rng.randint(1, 60)))
    for _ in range(extra_factor * V):           # extra roads, E is about 3V
        u, v = rng.randrange(V), rng.randrange(V)
        if u == v:
            v = (v + 1) % V
        roads.append((len(roads), u, v, rng.randint(1, 60)))
    return penalties, roads