"""
Unit Tests for Synthetic Data Generator (data_gen.py)
Tests schema, row volume, class balance, and reproducible random seeding.
"""
import pytest
import pandas as pd
from src.transport.data_gen import generate_ridership_dataset
from src.transport.utils import load_config

@pytest.fixture
def test_config():
    cfg = load_config()
    # Fast lightweight config for testing
    cfg["data"]["start_date"] = "2026-11-01"
    cfg["data"]["end_date"] = "2026-11-05"
    return cfg

def test_data_generation_columns(test_config):
    df = generate_ridership_dataset(test_config)
    expected_cols = [
        "date", "hour", "day_of_week", "is_weekend", "is_holiday",
        "weather", "route_id", "stop_id", "is_exam_or_event_day",
        "crowd_score", "crowd_level"
    ]
    for col in expected_cols:
        assert col in df.columns

def test_crowd_level_classes(test_config):
    df = generate_ridership_dataset(test_config)
    classes = set(df["crowd_level"].unique())
    assert classes.issubset({"Low", "Medium", "High"})
    assert len(classes) >= 2

def test_crowd_score_range(test_config):
    df = generate_ridership_dataset(test_config)
    assert (df["crowd_score"] >= 0.0).all()
    assert (df["crowd_score"] <= 1.0).all()

def test_data_reproducibility(test_config):
    df1 = generate_ridership_dataset(test_config)
    df2 = generate_ridership_dataset(test_config)
    assert df1.equals(df2)

def test_hour_bounds(test_config):
    df = generate_ridership_dataset(test_config)
    assert (df["hour"] >= 6).all()
    assert (df["hour"] <= 22).all()
