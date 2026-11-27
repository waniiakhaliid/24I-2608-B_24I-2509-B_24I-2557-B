import random
import pandas as pd
import pytest
from modules.routing import (build_graph, dijkstra, bellman_ford, bfs, route, walk, MinHeap,
                             RoutingInputError, case_graph, closed_for_day, DAY_TARGET)
from reference import route_bruteforce
import loader
from config import CACHE

needs_cache = pytest.mark.skipif(not (CACHE / "roads.csv").exists(),
                                 reason="run src/build_cache.py first")

# hand example: 0-1 (10), 1-2 (10), 0-2 (50), 2-3 (1); penalties 0,1,0,3
HAND_PEN = [0, 1, 0, 3]
HAND_ROADS = [(0, 0, 1, 10), (1, 1, 2, 10), (2, 0, 2, 50), (3, 2, 3, 1)]


def rand_instance(rng):
    n = rng.randint(1, 7)
    pen = [0] + [rng.choice([0, 1, 2, 4, 6]) for _ in range(n - 1)]
    roads = [(i, rng.randrange(n), rng.randrange(n), rng.randint(1, 60))
             for i in range(rng.randint(0, 10))]
    closed = {r[0] for r in roads if rng.random() < 0.25}
    return pen, roads, closed


def test_hand_example():
    adj = build_graph(HAND_PEN, HAND_ROADS)
    d = dijkstra(adj, 0)
    assert d.dist == [0, 11, 21, 25]
    assert route(d.parent, d.dist, 0, 3) == [0, 1, 2, 3]
    b = bfs(adj, 0)
    assert b.hops == [0, 1, 1, 2]
    assert route(b.parent, b.hops, 0, 2) == [0, 2]
    assert walk(adj, [0, 2])[0] == 50          # fewest roads costs 50 against 21


def test_unreachable_and_trivial():
    adj = build_graph([0, 0], [(0, 0, 1, 5)], closed={0})
    d = dijkstra(adj, 0)
    assert d.dist == [0, None] and route(d.parent, d.dist, 0, 1) is None
    assert bfs(adj, 0).hops == [0, None]
    assert dijkstra(build_graph([0], []), 0).dist == [0]
    assert route(d.parent, d.dist, 0, 0) == [0]


def test_bad_input_rejected():
    with pytest.raises(RoutingInputError):
        build_graph([], [])
    with pytest.raises(RoutingInputError):
        build_graph([0, 0], [(0, 0, 5, 3)])            # endpoint outside map
    with pytest.raises(RoutingInputError):
        build_graph([0, 0], [(0, 0, 1, 0)])            # minutes < 1
    with pytest.raises(RoutingInputError):
        build_graph([0, -1], [(0, 0, 1, 3)])           # negative penalty
    adj = build_graph([0, 0], [(0, 0, 1, 3)])
    for fn in (dijkstra, bellman_ford, bfs):
        for bad in (-1, 2, 1.5):
            with pytest.raises(RoutingInputError):
                fn(adj, bad)


def test_calendar_rules():
    assert build_graph([0, 0], [(0, 0, 1, 3)], storm=True)[0][0][1] == 5       # ceil(4.5)
    assert build_graph([0, 2], [(0, 0, 1, 3)], double_penalty=True)[0][0][1] == 7
    assert build_graph([0, 1], [(0, 0, 1, 3)], double_penalty=True)[0][0][1] == 4
    w = pd.DataFrame({"wave_no": [0, 0, 1, 2], "road_no": [10, 11, 12, 13]})
    assert closed_for_day(w, 1) == set()
    assert closed_for_day(w, 2) == {10, 11}
    assert closed_for_day(w, 3) == {12}
    assert closed_for_day(w, 5) == {10, 11}            # wave 3 mod 3 = wave 0
    assert closed_for_day(w, 6) == closed_for_day(w, 7) == {10, 11, 12, 13}
    assert closed_for_day(w.iloc[0:0], 4) == set()
    with pytest.raises(RoutingInputError):
        closed_for_day(w, 8)


def test_heap_sorts():
    rng = random.Random(84)
    xs = [(rng.randint(0, 50), rng.randint(0, 50)) for _ in range(200)]
    h = MinHeap()
    for x in xs:
        h.push(x)
    assert [h.pop() for _ in xs] == sorted(xs)


def test_random_against_bruteforce_and_bellman_ford():
    rng = random.Random(84)
    for _ in range(300):
        pen, roads, closed = rand_instance(rng)
        adj = build_graph(pen, roads, closed)
        ref = route_bruteforce(pen, roads, closed, 0)
        d, b = dijkstra(adj, 0), bellman_ford(adj, 0)
        assert d.dist == ref and b.dist == ref
        assert [h is not None for h in bfs(adj, 0).hops] == [x is not None for x in ref]


def route_invariants(adj, closed, path, cost, source, target):
    assert path[0] == source and path[-1] == target
    c, roads = walk(adj, path)                      # every step is an open road
    assert c == cost                                # route cost equals reported cost
    assert not set(roads) & closed                  # no closed road used


@needs_cache
def test_sample_cases_all_days():
    s = loader.sample_cases()
    for cid in s["case_id"]:
        case = loader.load_case(cid)
        for day in range(1, 8):
            adj, target, closed = case_graph(case, day)
            d, b, f = dijkstra(adj, 0), bellman_ford(adj, 0), bfs(adj, 0)
            assert d.dist == b.dist, f"{cid} day {day}: Dijkstra != Bellman-Ford"
            assert [x is None for x in d.dist] == [x is None for x in f.hops]
            path = route(d.parent, d.dist, 0, target)
            if path is not None:
                route_invariants(adj, closed, path, d.dist[target], 0, target)
            fp = route(f.parent, f.hops, 0, target)
            if fp is not None:
                assert walk(adj, fp)[0] >= d.dist[target]      # cheapest is never beaten


@needs_cache
def test_day1_destination_reachable_everywhere():
    for cid in loader.sample_cases()["case_id"]:
        adj, target, _ = case_graph(loader.load_case(cid), 1)
        assert dijkstra(adj, 0).dist[target] is not None, cid


@needs_cache
def test_all_waves_closed_blocks_exactly_the_union():
    for cid in ("1-00", "2-15", "7-47"):
        case = loader.load_case(cid)
        union = {int(r) for r in case["waves"]["road_no"]}
        adj1, _, _ = case_graph(case, 1)
        adj6, _, closed6 = case_graph(case, 6)
        assert closed6 == union                                   # day 6 closes exactly the union
        used = {rn for lst in adj6 for _, _, rn in lst}
        assert not used & union                                   # no closed road is in the graph
        r1 = {i for i, x in enumerate(dijkstra(adj1, 0).dist) if x is not None}
        r6 = {i for i, x in enumerate(dijkstra(adj6, 0).dist) if x is not None}
        assert r6 <= r1                                           # closing roads never adds reach


@needs_cache
def test_trap_48_fewest_roads_is_dearer():
    """If this fails, group 4's trap does not fool BFS: report it, do not hide it."""
    adj, target, _ = case_graph(loader.load_case("4-48"), 1)
    d, f = dijkstra(adj, 0), bfs(adj, 0)
    cheapest = d.dist[target]
    fewest = walk(adj, route(f.parent, f.hops, 0, target))[0]
    print(f"trap 4-48 target {target}: fewest-roads cost {fewest} / cheapest {cheapest} "
          f"= {fewest / cheapest:.2f}")
    assert fewest >= cheapest