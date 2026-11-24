"""
Unit Tests for Transit Network (network.py)
Tests reachability, symmetry, non-negative travel times, and adjacency list integrity.
"""
import pytest
from src.transport.network import TransitNetwork, STOPS_DATA, ROUTES_DATA

@pytest.fixture
def network():
    return TransitNetwork()

def test_stop_count(network):
    assert len(network.stops) >= 25
    assert len(network.get_all_stop_ids()) >= 25

def test_routes_count(network):
    assert len(network.routes) == 6

def test_stops_have_valid_coordinates(network):
    for stop_id, info in network.stops.items():
        assert "x" in info and "y" in info
        assert 26.0 <= info["x"] <= 28.0  # Latitude range
        assert 80.0 <= info["y"] <= 82.0  # Longitude range

def test_interchange_stops_exist(network):
    interchanges = network.get_interchange_stops()
    assert len(interchanges) >= 3
    assert "STOP_01" in interchanges or "STOP_03" in interchanges

def test_travel_times_within_bounds(network):
    for r_id, r_info in network.routes.items():
        for t in r_info["times"]:
            assert 3 <= t <= 9, f"Travel time {t} out of bounds in route {r_id}"

def test_adjacency_list_non_negative(network):
    for u, neighbors in network.adjacency_list.items():
        for v, travel_time, route_id in neighbors:
            assert travel_time > 0
            assert network.is_valid_stop(v)

def test_graph_bidirectional_symmetry(network):
    for u, neighbors in network.adjacency_list.items():
        for v, travel_time, route_id in neighbors:
            reverse_edges = [edge for edge in network.adjacency_list[v] if edge[0] == u and edge[2] == route_id]
            assert len(reverse_edges) > 0, f"Missing return edge from {v} to {u}"

def test_all_stops_have_neighbors(network):
    for stop_id in network.get_all_stop_ids():
        neighbors = network.get_neighbors(stop_id)
        assert len(neighbors) > 0, f"Isolated stop found: {stop_id}"
