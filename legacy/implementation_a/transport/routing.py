"""
Dijkstra Routing Engine with Custom Priority Queue (heapq)
Computes Baseline Shortest Path (lambda=0) vs. Multi-Objective Crowd-Aware Path.

Design Justification:
The Dijkstra routing algorithm is implemented from scratch using Python's standard `heapq` module
operating directly on the adjacency list. NetworkX is NOT used for path optimization, preserving
deterministic execution, transparent algorithmic verification, and strict memory efficiency.
"""
import heapq
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime

from src.transport.network import TransitNetwork
from src.transport.utils import load_config
from src.transport.model import CrowdModelManager

class DijkstraRouter:
    def __init__(self, network: TransitNetwork = None, model_mgr: CrowdModelManager = None, config: Dict[str, Any] = None):
        self.config = config or load_config()
        self.network = network or TransitNetwork()
        self.model_mgr = model_mgr
        self.crowd_penalties = self.config["routing"]["crowd_penalty_map"]
        self.transfer_penalty = float(self.config["routing"]["transfer_penalty"])

    def _ensure_model(self):
        if self.model_mgr is None:
            self.model_mgr = CrowdModelManager.load()

    def baseline_route(self, src: str, dst: str) -> Optional[Dict[str, Any]]:
        """Calculates traditional shortest-time route (lambda = 0.0, ignoring crowd congestion)."""
        return self._dijkstra_search(
            src=src,
            dst=dst,
            when=12,
            weather="clear",
            is_event=0,
            lam=0.0
        )

    def best_route(
        self,
        src: str,
        dst: str,
        when: Union[int, datetime] = 8,
        weather: str = "clear",
        is_event: int = 0,
        lam: float = None
    ) -> Optional[Dict[str, Any]]:
        """Calculates crowd-aware Pareto optimal route with tunable lambda (crowd vs. time trade-off)."""
        if lam is None:
            lam = float(self.config["routing"]["default_lambda"])
        return self._dijkstra_search(
            src=src,
            dst=dst,
            when=when,
            weather=weather,
            is_event=is_event,
            lam=lam
        )

    def _dijkstra_search(
        self,
        src: str,
        dst: str,
        when: Union[int, datetime],
        weather: str,
        is_event: int,
        lam: float
    ) -> Optional[Dict[str, Any]]:
        if not self.network.is_valid_stop(src) or not self.network.is_valid_stop(dst):
            return None

        if src == dst:
            return {
                "path": [src],
                "path_names": [self.network.get_stop_name(src)],
                "segments": [],
                "total_travel_time": 0.0,
                "total_crowd_penalty": 0.0,
                "total_cost": 0.0,
                "transfers": 0,
                "high_crowd_segments": 0
            }

        self._ensure_model()

        # Priority queue entry: (cost, counter, current_stop, last_route_id, path_segments)
        counter = 0
        queue: List[Tuple[float, int, str, Optional[str], List[Dict[str, Any]]]] = []
        heapq.heappush(queue, (0.0, counter, src, None, []))

        # Best cost tracker: (stop, last_route_id) -> cost
        best_costs: Dict[Tuple[str, Optional[str]], float] = {}

        while queue:
            cost, _, u, last_route, segments = heapq.heappop(queue)

            if u == dst:
                return self._format_result(src, dst, cost, segments)

            state = (u, last_route)
            if state in best_costs and best_costs[state] <= cost:
                continue
            best_costs[state] = cost

            for v, travel_time, route_id in self.network.get_neighbors(u):
                # 1. Predict crowd level on this segment
                crowd_level = self.model_mgr.predict_crowd(
                    route_id=route_id,
                    stop_id=v,
                    dt_or_hour=when,
                    weather=weather,
                    is_event=is_event
                )
                crowd_penalty = self.crowd_penalties.get(crowd_level, 1)

                # 2. Transfer penalty if switching bus lines
                transfer_cost = 0.0
                if last_route is not None and last_route != route_id:
                    transfer_cost = self.transfer_penalty

                # 3. Composite edge cost formula
                edge_cost = travel_time + (lam * crowd_penalty) + transfer_cost
                new_cost = cost + edge_cost

                seg_record = {
                    "from_stop": u,
                    "to_stop": v,
                    "from_name": self.network.get_stop_name(u),
                    "to_name": self.network.get_stop_name(v),
                    "route_id": route_id,
                    "travel_time": travel_time,
                    "crowd_level": crowd_level,
                    "crowd_penalty": crowd_penalty,
                    "transfer": 1 if (last_route and last_route != route_id) else 0
                }

                next_state = (v, route_id)
                if next_state not in best_costs or new_cost < best_costs[next_state]:
                    counter += 1
                    heapq.heappush(queue, (new_cost, counter, v, route_id, segments + [seg_record]))

        return None

    def _format_result(self, src: str, dst: str, total_cost: float, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        path = [src] + [s["to_stop"] for s in segments]
        path_names = [self.network.get_stop_name(s) for s in path]
        total_time = sum(s["travel_time"] for s in segments)
        total_crowd_penalty = sum(s["crowd_penalty"] for s in segments)
        transfers = sum(s["transfer"] for s in segments)
        high_crowd_count = sum(1 for s in segments if s["crowd_level"] == "High")

        return {
            "path": path,
            "path_names": path_names,
            "segments": segments,
            "total_travel_time": round(total_time, 1),
            "total_crowd_penalty": int(total_crowd_penalty),
            "total_cost": round(total_cost, 2),
            "transfers": transfers,
            "high_crowd_segments": high_crowd_count
        }
