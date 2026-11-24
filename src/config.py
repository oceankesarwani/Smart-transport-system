"""
System Configuration and Global Hyperparameters
"""
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"
MODELS_DIR = SRC_DIR / "model" / "artifacts"
DOCS_DIR = BASE_DIR / "docs"

# Data Files
STATIONS_FILE = DATA_DIR / "stations.csv"
ROUTES_FILE = DATA_DIR / "routes.csv"
HISTORICAL_CROWD_FILE = DATA_DIR / "historical_crowd.csv"
MODEL_FILE = MODELS_DIR / "crowd_predictor.pkl"

# Algorithm Hyperparameters (Cost Function Weights)
# Cost = w_time * travel_time + w_crowd * crowd_penalty + w_transfer * transfer_penalty
WEIGHT_TIME = 1.0
WEIGHT_CROWD = 2.5
WEIGHT_TRANSFER = 4.0  # Penalty in minutes per line interchange

# Congestion Thresholds (0.0 to 1.0)
CONGESTION_LOW = 0.35
CONGESTION_MODERATE = 0.70
CONGESTION_HIGH = 0.88

# Peak Hours Definition
PEAK_HOURS_MORNING = (8, 10)
PEAK_HOURS_EVENING = (17, 20)
