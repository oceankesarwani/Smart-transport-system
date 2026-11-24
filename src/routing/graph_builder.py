"""
Transit Network Graph Builder
Constructs a NetworkX MultiDiGraph representing stations, rail/bus corridors, and transfer points.
"""
import networkx as nx
import pandas as pd
from typing import Dict, Any
from src.pipeline.data_loader import DataLoader

class TransitGraphBuilder:
    @staticmethod
    def build_network_graph(stations_df: pd.DataFrame = None, routes_df: pd.DataFrame = None) -> nx.MultiDiGraph:
        """
        Creates a directed MultiGraph where:
        - Nodes represent stations with attributes (name, coordinates, capacity, zone, is_interchange).
        - Edges represent physical transit routes (line_name, line_type, distance_km, base_time_mins).
        """
        if stations_df is None:
            stations_df = DataLoader.load_stations()
        if routes_df is None:
            routes_df = DataLoader.load_routes(bidirectional=True)

        G = nx.MultiDiGraph()

        # Add station nodes
        for _, row in stations_df.iterrows():
            G.add_node(
                str(row["station_id"]),
                name=str(row["name"]),
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                capacity=int(row["capacity"]),
                is_interchange=int(row["is_interchange"]),
                zone=str(row["zone"])
            )

        # Add route edges
        for _, row in routes_df.iterrows():
            u = str(row["from_station"])
            v = str(row["to_station"])
            G.add_edge(
                u, v,
                key=str(row["route_id"]),
                route_id=str(row["route_id"]),
                line_name=str(row["line_name"]),
                line_type=str(row["line_type"]),
                distance_km=float(row["distance_km"]),
                base_time_mins=float(row["base_time_mins"])
            )

        return G
