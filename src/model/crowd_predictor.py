"""
Crowd Predictor Module
Implements cyclical feature engineering and Gradient Boosting / Random Forest regression
to predict platform and vehicle congestion index [0.0 - 1.0].
"""
import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, r2_score
from src.config import MODEL_FILE

class CrowdPredictor:
    def __init__(self):
        self.model = None
        self.feature_columns: List[str] = []
        self.station_encoder: Dict[str, int] = {}
        self.weather_mapping = {"Clear": 0, "Rain": 1, "Storm": 2}
        self.metrics: Dict[str, float] = {}

    def _engineer_features(self, df: pd.DataFrame, fit_encoder: bool = False) -> pd.DataFrame:
        df = df.copy()

        # Cyclical Hour encoding (preserves 23:00 -> 00:00 continuity)
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)

        # Cyclical Day of Week encoding (preserves Sunday -> Monday continuity)
        df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7.0)
        df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7.0)

        # Weather numeric encoding
        if "weather" in df.columns:
            df["weather_code"] = df["weather"].map(self.weather_mapping).fillna(0).astype(int)
        else:
            df["weather_code"] = 0

        # Special event and peak indicators
        if "special_event" not in df.columns:
            df["special_event"] = 0
        if "is_weekend" not in df.columns:
            df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        if "is_peak" not in df.columns:
            df["is_peak"] = df["hour"].apply(lambda h: 1 if (8 <= h <= 10 or 17 <= h <= 20) else 0)

        # One-Hot Encoding for Station IDs
        if fit_encoder:
            unique_stations = sorted(df["station_id"].unique())
            self.station_encoder = {st: idx for idx, st in enumerate(unique_stations)}

        # Create one-hot columns for stations
        for st in self.station_encoder:
            df[f"st_{st}"] = (df["station_id"] == st).astype(int)

        base_features = [
            "hour_sin", "hour_cos", "day_sin", "day_cos",
            "is_weekend", "is_peak", "weather_code", "special_event"
        ]
        station_features = [f"st_{st}" for st in self.station_encoder]
        self.feature_columns = base_features + station_features

        return df[self.feature_columns]

    def train_and_evaluate(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> Dict[str, Any]:
        """Trains multiple regressors, compares them, and selects the optimal model."""
        X_train = self._engineer_features(train_df, fit_encoder=True)
        y_train = train_df["congestion_index"].values

        X_test = self._engineer_features(test_df, fit_encoder=False)
        y_test = test_df["congestion_index"].values

        # Model benchmark dictionary
        candidate_models = {
            "Ridge Regression (Linear Baseline)": Ridge(alpha=1.0),
            "Random Forest Regressor (Tree Baseline)": RandomForestRegressor(n_estimators=60, max_depth=12, random_state=42, n_jobs=-1),
            "Gradient Boosting Regressor (Production SOTA)": GradientBoostingRegressor(n_estimators=100, learning_rate=0.08, max_depth=6, random_state=42)
        }

        benchmark_results = {}
        best_r2 = -float("inf")
        best_name = None

        for name, model_instance in candidate_models.items():
            model_instance.fit(X_train, y_train)
            preds = model_instance.predict(X_test)
            preds = np.clip(preds, 0.0, 1.0)

            rmse = float(root_mean_squared_error(y_test, preds))
            mae = float(mean_absolute_error(y_test, preds))
            r2 = float(r2_score(y_test, preds))
            # Mean Absolute Percentage Error (avoid division by 0)
            mape = float(np.mean(np.abs((y_test - preds) / np.maximum(y_test, 0.05))) * 100.0)

            benchmark_results[name] = {
                "RMSE": round(rmse, 4),
                "MAE": round(mae, 4),
                "R2": round(r2, 4),
                "MAPE_percent": round(mape, 2)
            }

            if r2 > best_r2:
                best_r2 = r2
                best_name = name
                self.model = model_instance

        self.metrics = benchmark_results[best_name]
        self.metrics["best_model_name"] = best_name
        self.metrics["all_benchmarks"] = benchmark_results

        return self.metrics

    def predict_single(self, station_id: str, hour: int, day_of_week: int = 1,
                       weather: str = "Clear", special_event: int = 0) -> float:
        """Predicts real-time congestion index for a single station."""
        row = pd.DataFrame([{
            "station_id": station_id,
            "hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": 1 if day_of_week >= 5 else 0,
            "is_peak": 1 if (8 <= hour <= 10 or 17 <= hour <= 20) else 0,
            "weather": weather,
            "special_event": special_event
        }])
        X = self._engineer_features(row, fit_encoder=False)
        pred = float(self.model.predict(X)[0])
        return round(float(np.clip(pred, 0.0, 1.0)), 3)

    def predict_network(self, station_ids: List[str], hour: int, day_of_week: int = 1,
                        weather: str = "Clear", special_event: int = 0) -> Dict[str, float]:
        """Predicts congestion for all stations simultaneously."""
        rows = [
            {
                "station_id": st,
                "hour": hour,
                "day_of_week": day_of_week,
                "is_weekend": 1 if day_of_week >= 5 else 0,
                "is_peak": 1 if (8 <= hour <= 10 or 17 <= hour <= 20) else 0,
                "weather": weather,
                "special_event": special_event
            }
            for st in station_ids
        ]
        df = pd.DataFrame(rows)
        X = self._engineer_features(df, fit_encoder=False)
        preds = self.model.predict(X)
        preds = np.clip(preds, 0.0, 1.0)
        return {st: round(float(p), 3) for st, p in zip(station_ids, preds)}

    def save(self, filepath: str = None) -> str:
        path = filepath or MODEL_FILE
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {
            "model": self.model,
            "feature_columns": self.feature_columns,
            "station_encoder": self.station_encoder,
            "metrics": self.metrics
        }
        joblib.dump(payload, path)
        return str(path)

    @classmethod
    def load(cls, filepath: str = None) -> "CrowdPredictor":
        path = filepath or MODEL_FILE
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found at: {path}")
        payload = joblib.load(path)
        predictor = cls()
        predictor.model = payload["model"]
        predictor.feature_columns = payload["feature_columns"]
        predictor.station_encoder = payload["station_encoder"]
        predictor.metrics = payload.get("metrics", {})
        return predictor
