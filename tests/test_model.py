"""
Unit Tests for Feature Engineering & Model Manager (features.py, model.py)
Tests pipeline transformation, model training, persistence, and dummy baseline comparison.
"""
import pytest
import numpy as np
import pandas as pd
from src.transport.features import FeaturePipeline
from src.transport.model import CrowdModelManager
from src.transport.utils import load_config

@pytest.fixture
def sample_ridership_df():
    records = []
    routes = ["R1", "R2", "R3"]
    stops = ["STOP_01", "STOP_02", "STOP_03"]
    for day in range(7):
        for h in range(6, 23):
            for r in routes:
                for s in stops:
                    score = 0.2 + (0.5 if 8 <= h <= 10 else 0.1)
                    lvl = "High" if score > 0.6 else ("Medium" if score > 0.35 else "Low")
                    records.append({
                        "hour": h,
                        "day_of_week": day,
                        "is_weekend": 1 if day >= 5 else 0,
                        "is_holiday": 0,
                        "weather": "clear",
                        "route_id": r,
                        "stop_id": s,
                        "is_exam_or_event_day": 0,
                        "crowd_level": lvl
                    })
    return pd.DataFrame(records)

def test_feature_pipeline_dimensions(sample_ridership_df):
    pipeline = FeaturePipeline()
    X_trans, y = pipeline.fit_transform(sample_ridership_df)
    assert X_trans.shape[0] == len(sample_ridership_df)
    assert X_trans.shape[1] > 10
    assert len(pipeline.feature_names) == X_trans.shape[1]

def test_cyclical_trigonometric_encodings(sample_ridership_df):
    pipeline = FeaturePipeline()
    X_df, _ = pipeline._prepare_dataframe(sample_ridership_df)
    assert "hour_sin" in X_df.columns and "hour_cos" in X_df.columns
    assert ((X_df["hour_sin"]**2 + X_df["hour_cos"]**2) - 1.0).abs().max() < 1e-4

def test_model_training_and_accuracy(sample_ridership_df):
    mgr = CrowdModelManager()
    metrics = mgr.train_and_benchmark(sample_ridership_df)
    assert "random_forest" in metrics
    rf_acc = metrics["random_forest"]["accuracy"]
    dummy_acc = metrics["dummy_baseline"]["accuracy"]
    assert rf_acc >= dummy_acc

def test_predict_crowd_output_labels(sample_ridership_df):
    mgr = CrowdModelManager()
    mgr.train_and_benchmark(sample_ridership_df)
    pred = mgr.predict_crowd("R1", "STOP_01", dt_or_hour=9, weather="clear")
    assert pred in ["Low", "Medium", "High"]

def test_model_save_and_load(tmp_path, sample_ridership_df):
    mgr = CrowdModelManager()
    mgr.train_and_benchmark(sample_ridership_df)
    save_file = str(tmp_path / "test_model.pkl")
    mgr.save(save_file)

    loaded_mgr = CrowdModelManager.load(save_file)
    pred = loaded_mgr.predict_crowd("R1", "STOP_01", dt_or_hour=9)
    assert pred in ["Low", "Medium", "High"]
