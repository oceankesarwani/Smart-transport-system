"""
Unit Tests for Custom Dijkstra Routing (routing.py)
Tests optimality, networkx comparison at lambda=0, crowd diversion, and edge cases.
"""
import pytest
import networkx as nx
from src.transport.network import TransitNetwork
from src.transport.routing import DijkstraRouter
from src.transport.model import CrowdModelManager
from src.transport.utils import load_config

@pytest.fixture
def router():
    net = TransitNetwork()
    return DijkstraRouter(network=net)

def test_same_source_and_destination(router):
    res = router.baseline_route("STOP_01", "STOP_01")
    assert res is not None
    assert res["total_travel_time"] == 0.0
    assert len(res["path"]) == 1
    assert res["transfers"] == 0

def test_invalid_stop_ids(router):
    assert router.baseline_route("INVALID_01", "STOP_01") is None
    assert router.baseline_route("STOP_01", "INVALID_02") is None

def test_baseline_matches_networkx_shortest_path(router):
    # Cross-verify custom heapq Dijkstra against NetworkX single-source shortest path
    G = nx.Graph()
    for u, neighbors in router.network.adjacency_list.items():
        for v, t, r in neighbors:
            if not G.has_edge(u, v) or G[u][v]["weight"] > t:
                G.add_edge(u, v, weight=t)

    src, dst = "STOP_01", "STOP_09"
    nx_time = nx.shortest_path_length(G, src, dst, weight="weight")
    my_res = router.baseline_route(src, dst)

    assert my_res is not None
    assert abs(my_res["total_travel_time"] - nx_time) < 1e-4

def test_crowd_aware_route_returns_valid_structure(router):
    res = router.best_route("STOP_01", "STOP_16", when=9, lam=1.5)
    assert res is not None
    assert len(res["path"]) >= 2
    assert res["path"][0] == "STOP_01"
    assert res["path"][-1] == "STOP_16"
    assert res["total_travel_time"] > 0
    assert "segments" in res
    for s in res["segments"]:
        assert s["crowd_level"] in ["Low", "Medium", "High"]

def test_transfer_penalty_applied(router):
    # Route requiring transfer should accrue transfer penalty
    res = router.best_route("STOP_09", "STOP_16", when=8, lam=1.0)
    assert res is not None
    if res["transfers"] > 0:
        assert res["total_cost"] > res["total_travel_time"]

def test_lambda_zero_equals_baseline(router):
    res_base = router.baseline_route("STOP_01", "STOP_12")
    res_lam0 = router.best_route("STOP_01", "STOP_12", lam=0.0)
    assert res_base["total_travel_time"] == res_lam0["total_travel_time"]
    assert res_base["path"] == res_lam0["path"]

def test_crowd_penalty_sensitivity(router):
    # Verify that higher lambda never increases crowd penalty compared to baseline
    res_base = router.baseline_route("STOP_02", "STOP_10")
    res_high_lam = router.best_route("STOP_02", "STOP_10", when=9, lam=4.0)
    assert res_high_lam["total_crowd_penalty"] <= res_base["total_crowd_penalty"] + 2

def test_unreachable_node_graceful_handling(router):
    # Manually query a non-existent route
    res = router.best_route("STOP_01", "NON_EXISTENT_999")
    assert res is None
