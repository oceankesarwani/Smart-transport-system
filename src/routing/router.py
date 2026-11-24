"""
Smart Transit Router Engine
Implements Naive Shortest Path (Standard Dijkstra) vs. weighted crowd-aware Dijkstra.
Outputs route itinerary, crowd exposure analysis, and performance delta.
"""
import heapq
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from src.routing.graph_builder import TransitGraphBuilder
from src.routing.cost_functions import calculate_edge_cost, compute_congestion_penalty, nonnegative
from src.config import WEIGHT_TIME, WEIGHT_CROWD, WEIGHT_TRANSFER

class SmartTransitRouter:
    def __init__(self, graph: Optional[nx.MultiDiGraph] = None):
        self.graph = graph if graph is not None else TransitGraphBuilder.build_network_graph()

    def find_naive_route(self, origin: str, destination: str, crowd_map: Optional[Dict[str, float]] = None) -> Optional[Dict[str, Any]]:
        """
        Calculates traditional shortest travel time route using Standard Dijkstra.
        Ignores crowd congestion during routing decisions (w_crowd = 0.0),
        but evaluates the actual crowd exposure using crowd_map if provided.
        """
        return self._search_path(
            origin=origin,
            destination=destination,
            crowd_map=crowd_map,
            w_time=1.0,
            w_crowd=0.0,
            w_transfer=WEIGHT_TRANSFER
        )

    def find_crowd_aware_route(
        self,
        origin: str,
        destination: str,
        crowd_map: Dict[str, float],
        comfort_preference: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates crowd-optimized route using weighted Dijkstra.
        Penalizes overcrowded stations and balances commute duration with passenger comfort.
        comfort_preference (0.0 = Pure Speed, 1.0 = Balanced, 2.0 = Maximum Comfort/Low Crowds).
        """
        w_crowd = WEIGHT_CROWD * nonnegative(comfort_preference, "comfort_preference")
        return self._search_path(
            origin=origin,
            destination=destination,
            crowd_map=crowd_map,
            w_time=WEIGHT_TIME,
            w_crowd=w_crowd,
            w_transfer=WEIGHT_TRANSFER
        )

    def _search_path(
        self,
        origin: str,
        destination: str,
        crowd_map: Optional[Dict[str, float]],
        w_time: float,
        w_crowd: float,
        w_transfer: float
    ) -> Optional[Dict[str, Any]]:
        if origin not in self.graph:
            raise ValueError(f"Origin station '{origin}' not found in network.")
        if destination not in self.graph:
            raise ValueError(f"Destination station '{destination}' not found in network.")
        nonnegative(w_time, "weight_time")
        nonnegative(w_crowd, "weight_crowd")
        nonnegative(w_transfer, "transfer_minutes")
        if crowd_map is not None:
            if set(self.graph) - set(crowd_map):
                raise ValueError("Crowd predictions required for every station")
            for value in crowd_map.values():
                compute_congestion_penalty(value)
        for _, _, data in self.graph.edges(data=True):
            nonnegative(data["base_time_mins"], "base_time")
            nonnegative(data.get("distance_km", 0), "distance")

        # Priority Queue for Dijkstra: (cost, count, current_node, current_line, path_records)
        # Sequence counter prevents comparing dict elements in path_edges during tie breaks
        counter = 0
        queue: List[Tuple[float, int, str, Optional[str], List[Dict[str, Any]]]] = []
        heapq.heappush(queue, (0.0, counter, origin, None, []))

        # Best cost map: (node, last_line) -> cost
        best_costs: Dict[Tuple[str, Optional[str]], float] = {}

        while queue:
            cost, _, u, last_line, path_edges = heapq.heappop(queue)

            if u == destination:
                return self._compile_route_result(origin, destination, cost, path_edges, crowd_map)

            state_key = (u, last_line)
            if state_key in best_costs and best_costs[state_key] <= cost:
                continue
            best_costs[state_key] = cost

            for v in self.graph.neighbors(u):
                edge_dict = self.graph[u][v]
                for key, edge_data in edge_dict.items():
                    line_name = edge_data.get("line_name", "")
                    base_time = edge_data.get("base_time_mins", 5.0)
                    dist = edge_data.get("distance_km", 2.0)
                    dest_crowd = crowd_map.get(v, 0.20) if crowd_map else 0.0

                    step_cost = calculate_edge_cost(
                        base_time=base_time,
                        dest_congestion=dest_crowd,
                        current_line=last_line,
                        next_line=line_name,
                        weight_time=w_time,
                        weight_crowd=w_crowd,
                        weight_transfer=w_transfer
                    )

                    new_cost = cost + step_cost
                    edge_record = {
                        "from_station": u,
                        "to_station": v,
                        "line_name": line_name,
                        "line_type": edge_data.get("line_type", "Metro"),
                        "distance_km": dist,
                        "base_time_mins": base_time,
                        "dest_crowd": dest_crowd
                    }
                    new_path = path_edges + [edge_record]

                    next_state = (v, line_name)
                    if next_state not in best_costs or new_cost < best_costs[next_state]:
                        counter += 1
                        heapq.heappush(queue, (new_cost, counter, v, line_name, new_path))

        return None  # No path exists

    def _compile_route_result(
        self,
        origin: str,
        destination: str,
        effective_cost: float,
        path_edges: List[Dict[str, Any]],
        crowd_map: Optional[Dict[str, float]]
    ) -> Dict[str, Any]:
        stations = [origin] + [e["to_station"] for e in path_edges]
        station_names = [self.graph.nodes[s].get("name", s) for s in stations]

        in_vehicle_time = sum(e["base_time_mins"] for e in path_edges)
        total_dist = sum(e["distance_km"] for e in path_edges)

        transfers = 0
        last_line = None
        for e in path_edges:
            if last_line is not None and e["line_name"] != last_line:
                transfers += 1
            last_line = e["line_name"]

        transfer_time = transfers * WEIGHT_TRANSFER
        total_time = in_vehicle_time + transfer_time

        congestion_vals = [crowd_map.get(s, 0.2) for s in stations] if crowd_map else [0.2] * len(stations)
        avg_congestion = sum(congestion_vals) / len(congestion_vals)
        max_congestion = max(congestion_vals)

        bottlenecks = [
            {"station_id": s, "name": name, "congestion": cong}
            for s, name, cong in zip(stations, station_names, congestion_vals)
            if cong >= 0.70
        ]

        return {
            "origin": origin,
            "destination": destination,
            "stations": stations,
            "station_names": station_names,
            "total_time_mins": total_time,
            "in_vehicle_time_mins": in_vehicle_time,
            "transfer_time_mins": transfer_time,
            "total_distance_km": round(total_dist, 1),
            "transfers": transfers,
            "effective_cost": effective_cost,
            "avg_congestion": avg_congestion,
            "max_congestion": max_congestion,
            "bottlenecks": bottlenecks,
            "segments": path_edges
        }

    def compare_routes(
        self,
        origin: str,
        destination: str,
        crowd_map: Dict[str, float],
        comfort_preference: float = 1.0
    ) -> Dict[str, Any]:
        """Compares Naive Shortest Path against Smart Crowd-Aware Route."""
        naive = self.find_naive_route(origin, destination, crowd_map=crowd_map)
        smart = self.find_crowd_aware_route(origin, destination, crowd_map, comfort_preference)

        if not naive or not smart:
            return {"status": "FAILED", "message": "Route path could not be computed."}

        # Performance analytics
        crowd_reduction_pct = 0.0
        if naive["avg_congestion"] > 0:
            crowd_reduction_pct = ((naive["avg_congestion"] - smart["avg_congestion"]) / naive["avg_congestion"]) * 100.0

        bottlenecks_bypassed = len(naive["bottlenecks"]) - len(smart["bottlenecks"])
        time_difference_mins = round(smart["total_time_mins"] - naive["total_time_mins"], 1)

        return {
            "status": "SUCCESS",
            "naive_route": naive,
            "smart_route": smart,
            "analytics": {
                "crowd_reduction_percent": crowd_reduction_pct,
                "bottlenecks_avoided": bottlenecks_bypassed,
                "naive_bottlenecks_count": len(naive["bottlenecks"]),
                "smart_bottlenecks_count": len(smart["bottlenecks"]),
                "travel_time_delta_mins": time_difference_mins,
                "is_different_path": [(s["to_station"], s["line_name"]) for s in naive["segments"]] != [(s["to_station"], s["line_name"]) for s in smart["segments"]]
            }
        }
