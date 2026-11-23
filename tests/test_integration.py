"""
Integration Tests for End-to-End Pipeline
Validates data ingestion -> model forecast -> graph routing -> comparative analytics
"""
import pytest
from SRC.pipeline.data_loader import DataLoader
from SRC.model.crowd_predictor import CrowdPredictor
from SRC.routing.router import SmartTransitRouter

def test_end_to_end_system_pipeline():
    # 1. Load components
    stations_df = DataLoader.load_stations()
    routes_df = DataLoader.load_routes()
    crowd_df = DataLoader.load_crowd_data()

    assert len(stations_df) == 20
    assert len(routes_df) > 30

    # 2. Train and obtain predictions
    predictor = CrowdPredictor()
    split = int(len(crowd_df) * 0.8)
    predictor.train_and_evaluate(crowd_df.iloc[:split], crowd_df.iloc[split:])

    all_stations = list(stations_df["station_id"])
    morning_crowd = predictor.predict_network(all_stations, hour=9, day_of_week=1, weather="Clear")
    assert len(morning_crowd) == 20

    # 3. Optimize route from Airport (S08) to TechZone/IIIT (S09)
    router = SmartTransitRouter()
    comparison = router.compare_routes(
        origin="S08",
        destination="S09",
        crowd_map=morning_crowd,
        comfort_preference=1.5
    )

    assert comparison["status"] == "SUCCESS"
    analytics = comparison["analytics"]
    assert "crowd_reduction_percent" in analytics
    assert "travel_time_delta_mins" in analytics

    smart = comparison["smart_route"]
    assert smart["stations"][0] == "S08"
    assert smart["stations"][-1] == "S09"
    assert smart["total_time_mins"] > 0
