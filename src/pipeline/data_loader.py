"""
Data Loader and Validator Module
Ensures strict schema validation, type integrity, and bidirectional route construction.
"""
import os
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from src.config import STATIONS_FILE, ROUTES_FILE, HISTORICAL_CROWD_FILE

REQUIRED_STATION_COLS = ["station_id", "name", "latitude", "longitude", "capacity", "is_interchange"]
REQUIRED_ROUTE_COLS = ["route_id", "line_name", "line_type", "from_station", "to_station", "distance_km", "base_time_mins"]
REQUIRED_CROWD_COLS = ["station_id", "hour", "day_of_week", "is_weekend", "is_peak", "congestion_index", "timestamp", "weather", "special_event"]

class DataLoader:
    @staticmethod
    def load_stations(filepath: str = None) -> pd.DataFrame:
        path = filepath or STATIONS_FILE
        if not os.path.exists(path):
            raise FileNotFoundError(f"Stations dataset not found at: {path}")
        df = pd.read_csv(path)
        for col in REQUIRED_STATION_COLS:
            if col not in df.columns:
                raise ValueError(f"Missing required station column: '{col}'")
        df["station_id"] = df["station_id"].astype(str).str.strip()
        df["latitude"] = df["latitude"].astype(float)
        df["longitude"] = df["longitude"].astype(float)
        df["capacity"] = df["capacity"].astype(int)
        df["is_interchange"] = df["is_interchange"].astype(int)
        if df.empty or df.isna().any().any() or df.station_id.duplicated().any():
            raise ValueError("Stations must be nonempty, complete and unique")
        if not (df.latitude.between(-90, 90).all() and df.longitude.between(-180, 180).all() and (df.capacity > 0).all()):
            raise ValueError("Invalid station coordinates or capacity")
        return df

    @staticmethod
    def load_routes(filepath: str = None, bidirectional: bool = True) -> pd.DataFrame:
        path = filepath or ROUTES_FILE
        if not os.path.exists(path):
            raise FileNotFoundError(f"Routes dataset not found at: {path}")
        df = pd.read_csv(path)
        for col in REQUIRED_ROUTE_COLS:
            if col not in df.columns:
                raise ValueError(f"Missing required route column: '{col}'")
        df["from_station"] = df["from_station"].astype(str).str.strip()
        df["to_station"] = df["to_station"].astype(str).str.strip()
        df["distance_km"] = df["distance_km"].astype(float)
        df["base_time_mins"] = df["base_time_mins"].astype(float)
        
        if df.empty or df.isna().any().any():
            raise ValueError("Routes must be nonempty and complete")
        for col in ["distance_km", "base_time_mins"]:
            if not np.isfinite(df[col]).all() or (df[col] < 0).any():
                raise ValueError(f"Invalid non-negative route value: {col}")
        if bidirectional:
            reversed_df = df.copy()
            reversed_df["from_station"] = df["to_station"]
            reversed_df["to_station"] = df["from_station"]
            reversed_df["route_id"] = df["route_id"] + "_REV"
            df = pd.concat([df, reversed_df], ignore_index=True).drop_duplicates(
                subset=["line_name", "from_station", "to_station"]
            )
        return df

    @staticmethod
    def load_crowd_data(filepath: str = None) -> pd.DataFrame:
        path = filepath or HISTORICAL_CROWD_FILE
        if not os.path.exists(path):
            raise FileNotFoundError(f"Crowd dataset not found at: {path}")
        df = pd.read_csv(path)
        for col in REQUIRED_CROWD_COLS:
            if col not in df.columns:
                raise ValueError(f"Missing required crowd column: '{col}'")
        df["station_id"] = df["station_id"].astype(str).str.strip()
        df["hour"] = df["hour"].astype(int)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
        if df.empty or df.isna().any().any():
            raise ValueError("Crowd data must be nonempty and complete")
        for col, lo, hi in [("hour", 0, 23), ("day_of_week", 0, 6), ("congestion_index", 0, 1), ("special_event", 0, 1)]:
            if not df[col].between(lo, hi).all():
                raise ValueError(f"Invalid range: {col}")
        if not df.weather.isin(["Clear", "Rain", "Storm"]).all():
            raise ValueError("Invalid weather")
        if not ((df.timestamp.dt.hour == df.hour) & (df.timestamp.dt.dayofweek == df.day_of_week)).all():
            raise ValueError("Timestamp context mismatch")
        if df.duplicated(["timestamp", "station_id"]).any():
            raise ValueError("Duplicate station timestamp")
        df = df.sort_values(["timestamp", "station_id"]).reset_index(drop=True)
        return df

    @classmethod
    def load_all(cls) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        return cls.load_stations(), cls.load_routes(), cls.load_crowd_data()
