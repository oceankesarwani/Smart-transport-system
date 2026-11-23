"""
Model Training & Evaluation Script (CLI Entrypoint)
Splits data temporally, trains ML models, benchmarks them, and saves the production weights.
"""
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from SRC.pipeline.data_loader import DataLoader
from SRC.model.crowd_predictor import CrowdPredictor
from SRC.config import MODEL_FILE, HISTORICAL_CROWD_FILE

def train_model():
    print("=" * 70)
    print(" Smart Public Transport System: Crowd Predictor Model Training ")
    print("=" * 70)

    # 1. Load Data
    print(f"[*] Loading historical dataset from: {HISTORICAL_CROWD_FILE}")
    df = DataLoader.load_crowd_data(str(HISTORICAL_CROWD_FILE))
    print(f"    Loaded {len(df):,} total records.")

    # 2. Chronological Train-Test Split (80% Train, 20% Test)
    # Temporal splitting ensures zero future-data leakage
    split_idx = int(len(df) * 0.80)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    print(f"[*] Chronological Split: {len(train_df):,} Train samples | {len(test_df):,} Test samples")

    # 3. Model Benchmark & Training
    predictor = CrowdPredictor()
    print("[*] Training candidate models & comparing performance metrics...")
    metrics = predictor.train_and_evaluate(train_df, test_df)

    print("\n" + "-" * 70)
    print(" MODEL BENCHMARK RESULTS ")
    print("-" * 70)
    for model_name, bench in metrics["all_benchmarks"].items():
        print(f" -> {model_name}:")
        print(f"      RMSE: {bench['RMSE']:.4f} | MAE: {bench['MAE']:.4f} | R² Score: {bench['R2']:.4f} | MAPE: {bench['MAPE_percent']:.2f}%")

    print(f"\n[+] Selected Best Model: {metrics['best_model_name']}")
    print(f"    Best R² Score: {metrics['R2']:.4f} (Accuracy Explaining Variance)")

    # 4. Save Model
    saved_path = predictor.save(str(MODEL_FILE))
    print(f"[+] Model artifact successfully exported to: {saved_path}")
    print("=" * 70)
    return metrics

if __name__ == "__main__":
    train_model()
