"""
Feature Engineering and Data Preprocessing Pipeline
Extracts cyclical time encodings, one-hot encodes categorical factors, and prepares train/test splits.
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Any
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

class FeaturePipeline:
    def __init__(self):
        self.preprocessor = None
        self.feature_names: List[str] = []

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        X_df, y = self._prepare_dataframe(df)
        self._build_preprocessor()
        X_trans = self.preprocessor.fit_transform(X_df)
        X_trans = np.asarray(X_trans, dtype=np.float64)
        if y is not None:
            y = np.asarray(y, dtype=str)
        self.feature_names = self._extract_feature_names()
        return X_trans, y

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        X_df, _ = self._prepare_dataframe(df, is_training=False)
        X_trans = self.preprocessor.transform(X_df)
        return np.asarray(X_trans, dtype=np.float64)

    def _prepare_dataframe(self, df: pd.DataFrame, is_training: bool = True) -> Tuple[pd.DataFrame, Any]:
        df = df.copy()

        # Cyclical trigonometric hour encoding
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)

        # Cyclical day of week encoding
        df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7.0)
        df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7.0)

        # Standardize event column name
        if "is_exam_or_event_day" in df.columns:
            df["is_event"] = df["is_exam_or_event_day"].astype(int)
        elif "is_event" not in df.columns:
            df["is_event"] = 0

        y = np.asarray(df["crowd_level"].tolist(), dtype=str) if is_training and "crowd_level" in df.columns else None
        return df, y

    def _build_preprocessor(self):
        categorical_cols = ["weather", "route_id", "stop_id"]
        numerical_cols = [
            "hour", "hour_sin", "hour_cos", "day_of_week", "day_sin", "day_cos",
            "is_weekend", "is_holiday", "is_event"
        ]

        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", "passthrough", numerical_cols),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols)
            ]
        )

    def _extract_feature_names(self) -> List[str]:
        numerical_cols = [
            "hour", "hour_sin", "hour_cos", "day_of_week", "day_sin", "day_cos",
            "is_weekend", "is_holiday", "is_event"
        ]
        cat_encoder = self.preprocessor.named_transformers_["cat"]
        cat_features = list(cat_encoder.get_feature_names_out(["weather", "route_id", "stop_id"]))
        return numerical_cols + cat_features
