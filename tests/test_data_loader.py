"""
Unit Tests for DataLoader and Schema Integrity
"""
import pytest
import pandas as pd
from src.pipeline.data_loader import DataLoader
from src.config import STATIONS_FILE, ROUTES_FILE, HISTORICAL_CROWD_FILE

def test_load_stations():
    df = DataLoader.load_stations(str(STATIONS_FILE))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 20
    assert "station_id" in df.columns
    assert "latitude" in df.columns
    assert "longitude" in df.columns
    assert "capacity" in df.columns
    assert (df["capacity"] > 0).all()
    # Coordinates for Lucknow should be around lat ~26.8, lon ~80.9
    assert ((df["latitude"] >= 26.0) & (df["latitude"] <= 28.0)).all()

def test_load_routes_bidirectional():
    df = DataLoader.load_routes(str(ROUTES_FILE), bidirectional=True)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 30
    assert "from_station" in df.columns
    assert "to_station" in df.columns
    assert (df["distance_km"] > 0).all()
    assert (df["base_time_mins"] > 0).all()

def test_load_crowd_data_schema():
    df = DataLoader.load_crowd_data(str(HISTORICAL_CROWD_FILE))
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 1000
    assert "congestion_index" in df.columns
    assert (df["congestion_index"] >= 0.0).all()
    assert (df["congestion_index"] <= 1.0).all()
