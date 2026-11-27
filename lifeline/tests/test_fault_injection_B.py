import random
import modules.routing as R
from modules.routing import build_graph, dijkstra, bfs, route, walk, RoutingInputError
from reference import route_bruteforce
from test_routing import rand_instance


def real(pen, roads, closed):
    return dijkstra(build_graph(pen, roads, closed), 0).dist


def wrong_penalty(pen, roads, closed):          # fault 1: penalty of the source, not the destination
    adj = [[] for _ in pen]
    for rn, u, v, m in roads:
        if rn not in closed:
            adj[u].append((v, m + pen[u], rn))
            adj[v].append((u, m + pen[v], rn))
    return dijkstra(adj, 0).dist


def ignore_closures(pen, roads, closed):        # fault 2: closed roads still used
    return dijkstra(build_graph(pen, roads, ()), 0).dist


def fewest_roads_cost(pen, roads, closed):      # fault 3: shortest-looks-cheapest (BFS route cost)
    adj = build_graph(pen, roads, closed)
    f = bfs(adj, 0)
    out = []
    for t in range(len(pen)):
        p = route(f.parent, f.hops, 0, t)
        out.append(None if p is None else walk(adj, p)[0])
    return out


def reference_check_fails(solver):
    """The reference check used by the real tests: compare with brute force."""
    rng = random.Random(84)
    for _ in range(300):
        pen, roads, closed = rand_instance(rng)
        if solver(pen, roads, closed) != route_bruteforce(pen, roads, closed, 0):
            return True
    return False


def test_real_dijkstra_passes_check():
    assert not reference_check_fails(real)


def test_fault_wrong_penalty_side_is_caught():
    assert reference_check_fails(wrong_penalty)


def test_fault_ignored_closures_is_caught():
    assert reference_check_fails(ignore_closures)


def test_fault_fewest_roads_instead_of_cheapest_is_caught():
    assert reference_check_fails(fewest_roads_cost)


def test_fault_missing_validation_is_caught(monkeypatch):
    monkeypatch.setattr(R, "check_source", lambda adj, s: None)    # remove the check
    adj = build_graph([0, 0], [(0, 0, 1, 3)])
    try:
        dijkstra(adj, 7)                 # source outside the map must be rejected
        rejected = False
    except RoutingInputError:
        rejected = True
    except Exception:                    # crashes instead of a clean error
        rejected = False
    assert not rejected                  # without validation the bad input is not rejected cleanly