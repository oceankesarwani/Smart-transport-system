"""
Dataset Generator for Smart Public Transport Route & Crowd Prediction System.
Generates realistic 60-day historical time-series sensor tap & platform congestion data.
Includes rush hours, weather anomalies, weekend patterns, and special event surges.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_crowd_data(output_path: str, seed: int = 42, days: int = 60):
    np.random.seed(seed)
    random.seed(seed)

    stations = [
        ("S01", 12000, "Central"),
        ("S02", 9500, "Central"),
        ("S03", 8000, "Commercial"),
        ("S04", 6000, "Administrative"),
        ("S05", 7500, "South"),
        ("S06", 5000, "Industrial"),
        ("S07", 6500, "Airport"),
        ("S08", 7000, "Airport"),
        ("S09", 8500, "TechZone"),
        ("S10", 5500, "Medical"),
        ("S11", 6500, "Suburban"),
        ("S12", 9000, "Residential"),
        ("S13", 7200, "Commercial"),
        ("S14", 10000, "East"),
        ("S15", 4500, "GreenZone"),
        ("S16", 5500, "Residential"),
        ("S17", 6000, "NorthEast"),
        ("S18", 6500, "Heritage"),
        ("S19", 5800, "OldCity"),
        ("S20", 6200, "North"),
    ]

    weather_types = ["Clear", "Rain", "Storm"]
    weather_weights = [0.75, 0.20, 0.05]

    start_date = datetime(2026, 9, 20, 5, 0, 0)
    records = []

    # Daily simulation
    for d in range(days):
        current_day = start_date + timedelta(days=d)
        is_weekend = 1 if current_day.weekday() >= 5 else 0
        day_of_week = current_day.weekday()

        # Day weather
        day_weather = np.random.choice(weather_types, p=weather_weights)
        weather_mult = 1.0
        if day_weather == "Rain":
            weather_mult = 1.25  # Rain increases crowd shift to transit
        elif day_weather == "Storm":
            weather_mult = 1.45

        # Random special events (e.g. Cricket match at Sports, Festival in Old City, Tech Conference)
        event_station = None
        if np.random.rand() < 0.15:
            event_station = np.random.choice(["S09", "S14", "S19", "S01"])

        # Hourly simulation (5 AM to 23 PM)
        for hour in range(5, 24):
            timestamp = current_day.replace(hour=hour, minute=0, second=0)

            # Determine peak hour factor
            # Morning peak: 8 AM - 10 AM, Evening peak: 17 PM - 20 PM
            is_peak = 0
            if not is_weekend:
                if 8 <= hour <= 10 or 17 <= hour <= 20:
                    is_peak = 1
                    time_factor = 2.4 if hour in [9, 18] else 1.9
                elif 12 <= hour <= 14:
                    time_factor = 1.2
                else:
                    time_factor = 0.65
            else:
                # Weekend pattern
                if 12 <= hour <= 19:
                    time_factor = 1.4
                    is_peak = 1 if 16 <= hour <= 19 else 0
                else:
                    time_factor = 0.55

            for st_id, capacity, zone in stations:
                special_event = 1 if (event_station == st_id and 16 <= hour <= 21) else 0

                # Base multiplier depends on zone and time
                zone_mult = 1.0
                if zone in ["TechZone", "Administrative"] and (8 <= hour <= 10) and not is_weekend:
                    zone_mult = 1.5
                elif zone in ["Residential"] and (17 <= hour <= 20) and not is_weekend:
                    zone_mult = 1.45
                elif zone in ["Commercial", "OldCity"] and is_weekend and (13 <= hour <= 20):
                    zone_mult = 1.4
                elif zone == "Central":
                    zone_mult = 1.35

                event_boost = 1.6 if special_event else 1.0

                # Mean inflow calculation
                base_inflow = (capacity * 0.08) * time_factor * zone_mult * weather_mult * event_boost
                noise = np.random.normal(0, base_inflow * 0.08)
                inflow = max(10, int(base_inflow + noise))

                # Outflow correlates with lag or time of day
                outflow_ratio = 0.9 + np.random.normal(0, 0.05)
                if 8 <= hour <= 10 and zone in ["TechZone", "Administrative"]:
                    outflow_ratio = 1.3
                elif 17 <= hour <= 20 and zone in ["TechZone", "Administrative"]:
                    outflow_ratio = 0.6
                outflow = max(10, int(inflow * outflow_ratio))

                # Congestion index (0.0 to 1.0)
                concurrent_load = inflow * 1.25
                congestion_index = min(1.0, round(concurrent_load / capacity, 3))

                # Congestion categorization
                if congestion_index < 0.35:
                    congestion_level = "LOW"
                elif congestion_index < 0.70:
                    congestion_level = "MODERATE"
                elif congestion_index < 0.88:
                    congestion_level = "HIGH"
                else:
                    congestion_level = "SEVERE"

                # Delay minutes associated with congestion
                base_delay = 0.5
                if congestion_index > 0.7:
                    base_delay += (congestion_index - 0.7) * 12.0
                delay_mins = round(max(0.0, base_delay + np.random.normal(0, 0.4)), 1)

                records.append({
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "station_id": st_id,
                    "hour": hour,
                    "day_of_week": day_of_week,
                    "is_weekend": is_weekend,
                    "is_peak": is_peak,
                    "weather": day_weather,
                    "special_event": special_event,
                    "inflow_count": inflow,
                    "outflow_count": outflow,
                    "congestion_index": congestion_index,
                    "congestion_level": congestion_level,
                    "delay_minutes": delay_mins
                })

    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} historical crowd records -> {output_path}")
    return df

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "historical_crowd.csv")
    generate_crowd_data(out, days=60)
