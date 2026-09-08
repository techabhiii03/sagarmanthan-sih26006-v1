"""
Central configuration for SagarManthan.
All tunable parameters live here or are loaded from environment variables.
No secrets are hardcoded.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List


class Settings:
    def __init__(self) -> None:
        self.frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        self.data_mode: str = os.getenv("DATA_MODE", "DEMO")
        self.demo_mode: bool = os.getenv("DEMO_MODE", "true").lower() in ("1", "true", "yes")
        self.data_random_seed: int = int(os.getenv("DATA_RANDOM_SEED", "42"))

        self.freight_data_provider: str = os.getenv("FREIGHT_DATA_PROVIDER", "synthetic")

        self.bunker_price_usd_mt: float = float(os.getenv("BUNKER_PRICE_USD_MT", "520.0"))
        self.usd_inr_rate: float = float(os.getenv("USD_INR_RATE", "83.50"))

        self.allow_estimated_distance: bool = os.getenv(
            "ALLOW_ESTIMATED_DISTANCE", "false"
        ).lower() in ("1", "true", "yes")
        self.estimated_distance_nm: float = float(os.getenv("ESTIMATED_DISTANCE_NM", "4500.0"))

        self.deadhead_cost_usd_per_nm: float = float(
            os.getenv("DEADHEAD_COST_USD_PER_NM", "0.15")
        )
        self.ballast_factor: float = float(os.getenv("BALLAST_FACTOR", "0.85"))
        self.handling_hire_fraction: float = float(
            os.getenv("HANDLING_HIRE_FRACTION", "0.30")
        )
        self.demurrage_waiting_fraction: float = float(
            os.getenv("DEMURRAGE_WAITING_FRACTION", "0.35")
        )

        self.forecast_interval_level: float = float(
            os.getenv("FORECAST_INTERVAL_LEVEL", "0.80")
        )
        self.walk_forward_min_train: int = int(os.getenv("WALK_FORWARD_MIN_TRAIN", "180"))
        self.walk_forward_step: int = int(os.getenv("WALK_FORWARD_STEP", "14"))


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_cors_origins() -> List[str]:
    raw = get_settings().frontend_origin
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins if origins else ["*"]
