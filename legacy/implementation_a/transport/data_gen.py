"""
Synthetic Ridership Dataset Generator Module
Generates ~60,000 realistic hourly transit ridership observations with known peak patterns,
weather effects, holiday factors, and class balances for Low, Medium, High crowd levels.

Note:
All ridership data is synthetic and systematically modeled after real-world urban transit
peak-hour dynamics because live passenger telemetry data is not publicly accessible.
"""
import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any

from src.transport.utils import load_config, get_project_root, ensure_dir
from src.transport.network import TransitNetwork

def generate_ridership_dataset(config: Dict[str, Any] = None) -> pd.DataFrame:
    if config is None:
        config = load_config()

    seed = config["project"]["seed"]
    np.random.seed(seed)
    random.seed(seed)

    network = TransitNetwork()
    raw_path = get_project_root() / config["data"]["raw_path"]
    sample_path = get_project_root() / "data" / "raw" / "sample_ridership.csv"
    ensure_dir(raw_path.parent)

    start_date = datetime.strptime(config["data"]["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(config["data"]["end_date"], "%Y-%m-%d")
    num_days = (end_date - start_date).days + 1

    low_max = config["data"]["crowd_thresholds"]["low_max"]
    medium_max = config["data"]["crowd_thresholds"]["medium_max"]

    # Base stop weights (higher for major hubs, college, market)
    stop_weights = {}
    for s_id, s_info in network.stops.items():
        st_type = s_info["type"]
        if st_type in ["Railway", "Terminal", "Interchange"]:
            stop_weights[s_id] = 1.45
        elif st_type in ["Market", "Commercial"]:
            stop_weights[s_id] = 1.30
        elif st_type in ["College", "TechZone"]:
            stop_weights[s_id] = 1.25
        elif st_type in ["Hospital", "Government"]:
            stop_weights[s_id] = 1.10
        else:
            stop_weights[s_id] = 0.85

    # Designated semester exam & festival dates
    exam_dates = {datetime(2026, 10, 15).date(), datetime(2026, 10, 16).date(),
                  datetime(2026, 11, 10).date(), datetime(2026, 11, 11).date()}
    holiday_dates = {datetime(2026, 10, 2).date(), datetime(2026, 10, 24).date(),
                     datetime(2026, 11, 1).date()}

    records = []

    # Iterate over all dates, routes, stops, and operating hours (6 to 22)
    for day_offset in range(num_days):
        current_date = (start_date + timedelta(days=day_offset)).date()
        day_of_week = current_date.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        is_holiday = 1 if current_date in holiday_dates else 0
        is_exam = 1 if current_date in exam_dates else 0

        # Day-level weather simulation (80% clear, 20% rain)
        weather_prob = 0.20 if current_date.month == 9 else 0.12
        weather = "rain" if np.random.rand() < weather_prob else "clear"

        for hour in range(config["data"]["hours"][0], config["data"]["hours"][1] + 1):
            # Hour multiplier: morning peak (8-10) and evening peak (17-19)
            if 8 <= hour <= 10:
                hour_factor = 1.85 if hour == 9 else 1.65
            elif 17 <= hour <= 19:
                hour_factor = 1.95 if hour == 18 else 1.70
            elif 12 <= hour <= 14:
                hour_factor = 1.15
            else:
                hour_factor = 0.65

            # Day context modifiers
            weekend_factor = 0.75 if is_weekend else 1.0
            holiday_factor = 0.45 if is_holiday else 1.0
            rain_factor = 1.25 if weather == "rain" else 1.0
            event_factor = 1.35 if is_exam else 1.0

            for route_id, route_info in network.routes.items():
                for stop_id in route_info["stops"]:
                    base_load = stop_weights.get(stop_id, 1.0)
                    # Crowd formula
                    score = (
                        base_load
                        * hour_factor
                        * weekend_factor
                        * holiday_factor
                        * rain_factor
                        * event_factor
                        * 0.28
                    )
                    # Add zero-mean Gaussian noise
                    noise = np.random.normal(0.0, 0.05)
                    normalized_score = float(np.clip(score + noise, 0.05, 1.0))

                    # Discrete category mapping
                    if normalized_score <= low_max:
                        crowd_level = "Low"
                    elif normalized_score <= medium_max:
                        crowd_level = "Medium"
                    else:
                        crowd_level = "High"

                    records.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "hour": hour,
                        "day_of_week": day_of_week,
                        "is_weekend": is_weekend,
                        "is_holiday": is_holiday,
                        "weather": weather,
                        "route_id": route_id,
                        "stop_id": stop_id,
                        "is_exam_or_event_day": 1 if is_exam else 0,
                        "crowd_score": round(normalized_score, 4),
                        "crowd_level": crowd_level
                    })

    df = pd.DataFrame(records)
    df.to_csv(raw_path, index=False)
    # Save a small sample (100 rows) for version control
    df.head(100).to_csv(sample_path, index=False)

    print(f"[+] Generated {len(df):,} synthetic ridership records -> {raw_path}")
    print("[-] Class Distribution:")
    for label, count in df["crowd_level"].value_counts().items():
        print(f"    • {label:6s}: {count:,} ({count / len(df) * 100:.1f}%)")

    return df

if __name__ == "__main__":
    generate_ridership_dataset()
