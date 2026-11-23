"""
Multi-Objective Cost Functions for Transit Routing
Calculates travel time, non-linear crowd penalty, and transfer penalties.
"""
from typing import Dict, Any

def compute_congestion_penalty(congestion_index: float) -> float:
    """
    Computes a non-linear passenger discomfort and platform bottleneck penalty.
    - Low (<= 0.35): Zero penalty, smooth boarding.
    - Moderate (0.35 - 0.70): Linear delay due to boarding queues.
    - Severe (> 0.70): Quadratic penalty reflecting extreme crowding, inability to board,
      and dwell time delays.
    """
    rho = max(0.0, min(1.0, float(congestion_index)))
    if rho <= 0.35:
        return 0.0
    elif rho <= 0.70:
        return (rho - 0.35) * 8.0
    else:
        # Extreme penalty curve for overcrowded transit coaches/stations
        return (0.35 * 8.0) + ((rho - 0.70) ** 2) * 35.0

def calculate_edge_cost(
    base_time: float,
    dest_congestion: float,
    current_line: str,
    next_line: str,
    weight_time: float = 1.0,
    weight_crowd: float = 2.5,
    weight_transfer: float = 4.0
) -> float:
    """
    Pareto Multi-Objective Edge Cost:
    C(e) = w_time * T(e) + w_crowd * Penalty(rho) + w_transfer * TransferCost
    """
    # 1. Base travel duration
    time_cost = weight_time * base_time

    # 2. Crowd Congestion Penalty
    crowd_penalty = weight_crowd * compute_congestion_penalty(dest_congestion)

    # 3. Line Interchange Transfer Penalty
    transfer_cost = 0.0
    if current_line and next_line and current_line != next_line:
        transfer_cost = weight_transfer * 4.0  # 4-minute average transfer walk + headway

    return time_cost + crowd_penalty + transfer_cost
