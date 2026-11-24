"""
Machine Learning Model Training, Cross-Validation & Prediction Module
Trains Random Forest with GridSearchCV against Logistic Regression and Dummy baselines.
"""
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Union
from datetime import datetime
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report
)

from src.transport.utils import load_config, get_project_root, ensure_dir
from src.transport.features import FeaturePipeline

class CrowdModelManager:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_config()
        self.pipeline = FeaturePipeline()
        self.model = None
        self.classes_ = ["Low", "Medium", "High"]
        self.metrics: Dict[str, Any] = {}

    def train_and_benchmark(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Trains candidate models, logs metrics, and selects best performing classifier."""
        X_trans, y = self.pipeline.fit_transform(df)

        # 80/20 Stratified train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_trans, y,
            test_size=self.config["model"]["test_size"],
            stratify=y,
            random_state=self.config["model"]["random_state"]
        )

        # 1. Baseline 1: Majority-class Dummy
        dummy = DummyClassifier(strategy="most_frequent")
        dummy.fit(X_train, y_train)
        dummy_preds = dummy.predict(X_test)
        dummy_acc = accuracy_score(y_test, dummy_preds)
        dummy_f1 = f1_score(y_test, dummy_preds, average="macro", zero_division=0)

        # 2. Baseline 2: Logistic Regression
        lr = LogisticRegression(max_iter=1000, random_state=42)
        lr.fit(X_train, y_train)
        lr_preds = lr.predict(X_test)
        lr_acc = accuracy_score(y_test, lr_preds)
        lr_f1 = f1_score(y_test, lr_preds, average="macro", zero_division=0)

        # 3. Production Model: Random Forest with fast GridSearchCV tuning
        param_grid = self.config["model"]["rf_param_grid"]
        tune_sample_size = min(6000, len(X_train))
        tune_indices = np.random.RandomState(42).choice(len(X_train), size=tune_sample_size, replace=False)
        X_tune, y_tune = X_train[tune_indices], y_train[tune_indices]

        rf_base = RandomForestClassifier(random_state=self.config["model"]["random_state"], n_jobs=-1)
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        grid_search = GridSearchCV(rf_base, param_grid, cv=cv, scoring="f1_macro", n_jobs=-1)
        grid_search.fit(X_tune, y_tune)

        best_rf = RandomForestClassifier(**grid_search.best_params_, random_state=self.config["model"]["random_state"], n_jobs=-1)
        best_rf.fit(X_train, y_train)
        rf_preds = best_rf.predict(X_test)

        rf_acc = accuracy_score(y_test, rf_preds)
        rf_f1 = f1_score(y_test, rf_preds, average="macro")
        rf_prec = precision_score(y_test, rf_preds, average="macro")
        rf_rec = recall_score(y_test, rf_preds, average="macro")
        cm = confusion_matrix(y_test, rf_preds, labels=self.classes_)

        # Feature importances
        importances = dict(zip(self.pipeline.feature_names, [round(float(v), 5) for v in best_rf.feature_importances_]))
        top_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:10]

        self.model = best_rf
        self.metrics = {
            "dummy_baseline": {"accuracy": round(float(dummy_acc), 4), "macro_f1": round(float(dummy_f1), 4)},
            "logistic_regression": {"accuracy": round(float(lr_acc), 4), "macro_f1": round(float(lr_f1), 4)},
            "random_forest": {
                "accuracy": round(float(rf_acc), 4),
                "macro_f1": round(float(rf_f1), 4),
                "precision": round(float(rf_prec), 4),
                "recall": round(float(rf_rec), 4),
                "best_params": grid_search.best_params_,
                "confusion_matrix": cm.tolist(),
                "top_features": top_importances
            }
        }

        print("[+] Model Benchmarking Completed:")
        print(f"    • Majority Dummy Baseline  : Acc={dummy_acc*100:.2f}%, F1={dummy_f1:.4f}")
        print(f"    • Logistic Regression      : Acc={lr_acc*100:.2f}%, F1={lr_f1:.4f}")
        print(f"    • Tuned Random Forest (SOTA): Acc={rf_acc*100:.2f}%, F1={rf_f1:.4f} (Best Params: {grid_search.best_params_})")

        return self.metrics

    def save(self, filepath: str = None):
        if filepath is None:
            filepath = str(get_project_root() / self.config["model"]["artifact_path"])
        ensure_dir(Path(filepath).parent)
        payload = {
            "model": self.model,
            "pipeline": self.pipeline,
            "metrics": self.metrics,
            "classes": self.classes_
        }
        joblib.dump(payload, filepath)
        print(f"[+] Model bundle saved -> {filepath}")

    @classmethod
    def load(cls, filepath: str = None) -> "CrowdModelManager":
        if filepath is None:
            config = load_config()
            filepath = str(get_project_root() / config["model"]["artifact_path"])
        payload = joblib.load(filepath)
        mgr = cls()
        mgr.model = payload["model"]
        mgr.pipeline = payload["pipeline"]
        mgr.metrics = payload["metrics"]
        mgr.classes_ = payload["classes"]
        return mgr

    def predict_crowd(
        self,
        route_id: str,
        stop_id: str,
        dt_or_hour: Union[int, datetime],
        weather: str = "clear",
        is_event: int = 0
    ) -> str:
        """Inference function returning predicted crowd category: Low, Medium, or High."""
        if isinstance(dt_or_hour, datetime):
            hour = dt_or_hour.hour
            day_of_week = dt_or_hour.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            is_holiday = 0
        else:
            hour = int(dt_or_hour)
            day_of_week = 1
            is_weekend = 0
            is_holiday = 0

        row = pd.DataFrame([{
            "hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "weather": weather.lower(),
            "route_id": route_id,
            "stop_id": stop_id,
            "is_event": int(is_event)
        }])

        X_trans = self.pipeline.transform(row)
        pred = self.model.predict(X_trans)[0]
        return str(pred)

if __name__ == "__main__":
    cfg = load_config()
    raw_csv = get_project_root() / cfg["data"]["raw_path"]
    if not os.path.exists(raw_csv):
        from src.transport.data_gen import generate_ridership_dataset
        generate_ridership_dataset(cfg)
    data = pd.read_csv(raw_csv)
    mgr = CrowdModelManager(cfg)
    mgr.train_and_benchmark(data)
    mgr.save()
