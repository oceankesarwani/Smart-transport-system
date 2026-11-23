"""
City Transit Network Module
Defines transit stops, 6 bus routes, and the city graph as an adjacency list.

Design Justification:
The graph is represented using an adjacency list (dict of lists of (neighbor, travel_time, route_id))
rather than an adjacency matrix because urban public transit networks are inherently sparse:
|E| ~ 2 * |V|. An adjacency matrix incurs O(|V|^2) space complexity and overhead traversing empty cells,
while an adjacency list requires only O(|V| + |E|) space and allows direct iteration over adjacent connections.
"""
from typing import Dict, List, Tuple, Any

# 25 named realistic city stops with geographic coordinates (lat, lon) and stop metadata
STOPS_DATA = {
    "STOP_01": {"name": "Central Railway Station", "x": 26.8322, "y": 80.9198, "type": "Railway", "is_interchange": True},
    "STOP_02": {"name": "City Bus Terminal", "x": 26.8152, "y": 80.9022, "type": "Terminal", "is_interchange": True},
    "STOP_03": {"name": "Hazratganj Commercial Plaza", "x": 26.8530, "y": 80.9450, "type": "Market", "is_interchange": True},
    "STOP_04": {"name": "Civil Secretariat", "x": 26.8439, "y": 80.9388, "type": "Government", "is_interchange": False},
    "STOP_05": {"name": "University Main Campus", "x": 26.8640, "y": 80.9360, "type": "College", "is_interchange": False},
    "STOP_06": {"name": "Medical College & Hospital", "x": 26.8710, "y": 80.9180, "type": "Hospital", "is_interchange": True},
    "STOP_07": {"name": "Chowk Heritage Bazaar", "x": 26.8680, "y": 80.9050, "type": "Market", "is_interchange": False},
    "STOP_08": {"name": "Aliganj Innovation Park", "x": 26.8910, "y": 80.9380, "type": "TechZone", "is_interchange": False},
    "STOP_09": {"name": "Engineering College Gate", "x": 26.9120, "y": 80.9420, "type": "College", "is_interchange": False},
    "STOP_10": {"name": "Munshi Pulia Intersection", "x": 26.8965, "y": 80.9920, "type": "Junction", "is_interchange": True},
    "STOP_11": {"name": "Indira Nagar Residential", "x": 26.8850, "y": 80.9850, "type": "Residential", "is_interchange": False},
    "STOP_12": {"name": "Polytechnic Interchange", "x": 26.8720, "y": 80.9980, "type": "Interchange", "is_interchange": True},
    "STOP_13": {"name": "Gomti Riverfront Park", "x": 26.8580, "y": 80.9650, "type": "Recreation", "is_interchange": False},
    "STOP_14": {"name": "Patrakarpuram Market", "x": 26.8505, "y": 80.9950, "type": "Market", "is_interchange": False},
    "STOP_15": {"name": "Gomti Nagar Extension", "x": 26.8385, "y": 81.0125, "type": "Residential", "is_interchange": True},
    "STOP_16": {"name": "IT City & IIIT Campus", "x": 26.7820, "y": 81.0250, "type": "College", "is_interchange": False},
    "STOP_17": {"name": "Medanta Multi-Specialty", "x": 26.7725, "y": 80.9980, "type": "Hospital", "is_interchange": False},
    "STOP_18": {"name": "Shaheed Path Junction", "x": 26.8040, "y": 81.0110, "type": "Junction", "is_interchange": False},
    "STOP_19": {"name": "Airport Cargo Terminal", "x": 26.7606, "y": 80.8893, "type": "Airport", "is_interchange": False},
    "STOP_20": {"name": "International Airport Hub", "x": 26.7570, "y": 80.8840, "type": "Airport", "is_interchange": False},
    "STOP_21": {"name": "Transport Nagar Industrial", "x": 26.7811, "y": 80.8765, "type": "Industrial", "is_interchange": False},
    "STOP_22": {"name": "Alambagh Metro Gateway", "x": 26.8150, "y": 80.9120, "type": "Interchange", "is_interchange": True},
    "STOP_23": {"name": "Kaiserbagh District Court", "x": 26.8580, "y": 80.9280, "type": "Government", "is_interchange": False},
    "STOP_24": {"name": "Mahanagar Central", "x": 26.8770, "y": 80.9520, "type": "Commercial", "is_interchange": False},
    "STOP_25": {"name": "Sports Stadium Arena", "x": 26.8290, "y": 80.9620, "type": "Stadium", "is_interchange": False}
}

# 6 defined bus routes connecting stops with travel times between 3 and 9 minutes
# Routes feature shared interchange stops (STOP_01, STOP_03, STOP_06, STOP_12, STOP_15) for real route options
ROUTES_DATA = {
    "R1": {
        "name": "Route 1 (North-South Trunk Line)",
        "stops": ["STOP_20", "STOP_19", "STOP_21", "STOP_02", "STOP_22", "STOP_01", "STOP_04", "STOP_03"],
        "times": [4, 7, 8, 5, 4, 4, 3]  # Travel times between consecutive stops
    },
    "R2": {
        "name": "Route 2 (East-West Express Line)",
        "stops": ["STOP_01", "STOP_03", "STOP_13", "STOP_14", "STOP_12", "STOP_11", "STOP_10"],
        "times": [3, 6, 5, 4, 4, 4]
    },
    "R3": {
        "name": "Route 3 (Tech & University Corridor)",
        "stops": ["STOP_03", "STOP_05", "STOP_24", "STOP_08", "STOP_09"],
        "times": [4, 5, 6, 6]
    },
    "R4": {
        "name": "Route 4 (South-East Highway Feeder)",
        "stops": ["STOP_01", "STOP_25", "STOP_15", "STOP_18", "STOP_17", "STOP_16"],
        "times": [7, 8, 5, 4, 4]
    },
    "R5": {
        "name": "Route 5 (Heritage & Healthcare Ring)",
        "stops": ["STOP_02", "STOP_01", "STOP_23", "STOP_06", "STOP_07", "STOP_08", "STOP_24", "STOP_12"],
        "times": [5, 4, 5, 4, 6, 5, 6]
    },
    "R6": {
        "name": "Route 6 (Outer Suburb Link)",
        "stops": ["STOP_12", "STOP_15", "STOP_18", "STOP_16"],
        "times": [6, 5, 4]
    }
}

class TransitNetwork:
    """Manages the transit graph as an adjacency list and queries network topology."""
    def __init__(self):
        self.stops = STOPS_DATA
        self.routes = ROUTES_DATA
        self.adjacency_list: Dict[str, List[Tuple[str, float, str]]] = {s: [] for s in self.stops}
        self._build_graph()

    def _build_graph(self):
        """Builds bidirectional adjacency list: u -> list of (v, travel_time, route_id)."""
        for r_id, r_info in self.routes.items():
            stops = r_info["stops"]
            times = r_info["times"]
            for i in range(len(stops) - 1):
                u, v = stops[i], stops[i + 1]
                t = float(times[i])
                # Forward edge
                self.adjacency_list[u].append((v, t, r_id))
                # Backward edge (bidirectional transit lines)
                self.adjacency_list[v].append((u, t, r_id))

    def get_neighbors(self, stop_id: str) -> List[Tuple[str, float, str]]:
        """Returns list of (neighbor_stop_id, travel_time_mins, route_id)."""
        return self.adjacency_list.get(stop_id, [])

    def get_stop_name(self, stop_id: str) -> str:
        return self.stops.get(stop_id, {}).get("name", stop_id)

    def is_valid_stop(self, stop_id: str) -> bool:
        return stop_id in self.stops

    def get_all_stop_ids(self) -> List[str]:
        return list(self.stops.keys())

    def get_interchange_stops(self) -> List[str]:
        return [s for s, info in self.stops.items() if info["is_interchange"]]
