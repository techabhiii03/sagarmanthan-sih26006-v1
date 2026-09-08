"""
Synthetic freight rate time-series generator for demonstration.
Generates realistic seasonal + trend + noise series for key routes / vessel classes.
All data labelled as DEMONSTRATION DATA.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple

# Base rates USD/MT (approx mid-2020s levels for coal routes)
BASE_RATES: Dict[str, Dict[str, float]] = {
    "Newcastle": {"Handysize": 22.0, "Supramax": 19.5, "Panamax": 17.8, "Capesize": 14.5},
    "Gladstone": {"Handysize": 21.0, "Supramax": 18.5, "Panamax": 16.8, "Capesize": 13.8},
    "Richards Bay": {"Handysize": 24.0, "Supramax": 21.0, "Panamax": 19.0, "Capesize": 15.5},
    "Maputo": {"Handysize": 26.0, "Supramax": 23.0, "Panamax": 20.5, "Capesize": 17.0},
    "Taboneo": {"Handysize": 18.0, "Supramax": 15.5, "Panamax": 14.0, "Capesize": 11.5},
    "Hampton Roads": {"Handysize": 32.0, "Supramax": 28.0, "Panamax": 25.5, "Capesize": 21.0},
}

def generate_freight_series(
    origin: str,
    vessel: str,
    days: int = 730,
    end_date: datetime | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate daily freight rate series with trend, seasonality, volatility."""
    rng = np.random.default_rng(seed + hash(origin + vessel) % 10000)
    if end_date is None:
        end_date = datetime(2026, 9, 6)
    start_date = end_date - timedelta(days=days - 1)
    dates = pd.date_range(start_date, end_date, freq="D")

    base = BASE_RATES.get(origin, {}).get(vessel, 18.0)

    # Components
    t = np.arange(len(dates))
    trend = 0.0015 * t  # mild upward long-term
    seasonal = 1.8 * np.sin(2 * np.pi * t / 365.25) + 0.9 * np.sin(4 * np.pi * t / 365.25)
    # short-term cycles
    cycle = 1.2 * np.sin(2 * np.pi * t / 45)
    noise = rng.normal(0, 0.85, size=len(dates))
    # occasional spikes
    spikes = np.zeros(len(dates))
    spike_idx = rng.choice(len(dates), size=8, replace=False)
    spikes[spike_idx] = rng.uniform(2.5, 5.5, size=8)

    rates = base + trend + seasonal + cycle + noise + spikes
    rates = np.clip(rates, base * 0.55, base * 1.85)

    # momentum features
    df = pd.DataFrame({"date": dates, "rate": rates})
    df["rate_ma7"] = df["rate"].rolling(7, min_periods=1).mean()
    df["rate_ma30"] = df["rate"].rolling(30, min_periods=1).mean()
    df["momentum_7"] = df["rate"] - df["rate"].shift(7)
    df["volatility_14"] = df["rate"].rolling(14, min_periods=1).std()
    df["origin"] = origin
    df["vessel"] = vessel
    return df.bfill().fillna(0)

def get_current_rate(origin: str, vessel: str) -> float:
    series = generate_freight_series(origin, vessel, days=60)
    return float(series["rate"].iloc[-1])
