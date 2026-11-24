"""Non-negative weighted costs. Crowd penalty is assumed discomfort, not delay."""
import math


def nonnegative(value, name):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def compute_congestion_penalty(congestion_index):
    rho = nonnegative(congestion_index, "congestion")
    if rho > 1:
        raise ValueError("congestion must be within [0, 1]")
    if rho <= 0.35:
        return 0.0
    if rho <= 0.70:
        return (rho - 0.35) * 8.0
    return 2.8 + (rho - 0.70) ** 2 * 35.0


def calculate_edge_cost(base_time, dest_congestion, current_line, next_line,
                        weight_time=1.0, weight_crowd=2.5, weight_transfer=4.0):
    time = nonnegative(base_time, "base_time")
    wt = nonnegative(weight_time, "weight_time")
    wc = nonnegative(weight_crowd, "weight_crowd")
    transfer = nonnegative(weight_transfer, "transfer_minutes")
    penalty = compute_congestion_penalty(dest_congestion)
    return wt * (time + (transfer if current_line is not None and current_line != next_line else 0)) + wc * penalty
