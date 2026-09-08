"""
Freight / market data provider abstraction.

Providers:
  - SyntheticFreightProvider  (default demo)
  - CSVFreightProvider        (loads real CSV; errors if invalid when selected)
  - ExternalFreightProvider   (stub for live APIs)

Switch via FREIGHT_DATA_PROVIDER env / settings.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd

from app.core.config import get_settings
from app.data.freight_generator import generate_freight_series, get_current_rate, BASE_RATES


class FreightDataProvider(ABC):
    @abstractmethod
    def get_series(self, origin: str, vessel: str, days: int = 540) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_current(self, origin: str, vessel: str) -> float:
        ...

    @abstractmethod
    def provenance(self) -> Dict[str, Any]:
        ...


class SyntheticFreightProvider(FreightDataProvider):
    def get_series(self, origin: str, vessel: str, days: int = 540) -> pd.DataFrame:
        seed = get_settings().data_random_seed
        return generate_freight_series(origin, vessel, days=days, seed=seed)

    def get_current(self, origin: str, vessel: str) -> float:
        return float(get_current_rate(origin, vessel))

    def provenance(self) -> Dict[str, Any]:
        return {
            "source_type": "synthetic_demo",
            "source_name": "SagarManthan SyntheticFreightProvider",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "limitations": [
                "Rates are synthetically generated for demonstration only",
                "Not live market data",
                "Calibrated to realistic bulk coal freight ranges",
            ],
            "base_rates_reference": {k: v for k, v in list(BASE_RATES.items())[:6]},
        }


class CSVFreightProvider(FreightDataProvider):
    """
    Load historical rates from a local CSV.
    Required columns: date, rate
    Optional columns: origin, vessel
    When FREIGHT_DATA_PROVIDER=csv, missing/invalid file raises — no silent synthetic fallback.
    """

    REQUIRED_COLS = {"date", "rate"}

    def __init__(self, path: Optional[str] = None):
        self.path = path or os.getenv("FREIGHT_CSV_PATH", "")

    def _load(self) -> pd.DataFrame:
        if not self.path or not os.path.isfile(self.path):
            raise FileNotFoundError(
                f"CSV freight provider selected but file not found: '{self.path}'. "
                "Set FREIGHT_CSV_PATH to a valid CSV with columns: date, rate [, origin, vessel]."
            )
        df = pd.read_csv(self.path)
        missing = self.REQUIRED_COLS - set(c.lower() for c in df.columns)
        # normalize columns
        colmap = {c: c.lower() for c in df.columns}
        df = df.rename(columns=colmap)
        missing = self.REQUIRED_COLS - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
        df = df.dropna(subset=["date", "rate"])
        df = df[df["rate"] > 0]
        if df.empty:
            raise ValueError("CSV contains no valid date/rate rows")
        df = df.sort_values("date").reset_index(drop=True)
        return df

    def get_series(self, origin: str, vessel: str, days: int = 540) -> pd.DataFrame:
        df = self._load()
        if "origin" in df.columns:
            df = df[df["origin"].astype(str).str.lower() == origin.lower()]
        if "vessel" in df.columns:
            df = df[df["vessel"].astype(str).str.lower() == vessel.lower()]
        if df.empty:
            raise ValueError(
                f"CSV has no rows for origin={origin!r} vessel={vessel!r}"
            )
        if days and len(df) > days:
            df = df.iloc[-days:].reset_index(drop=True)
        out = df[["date", "rate"]].copy()
        out["origin"] = origin
        out["vessel"] = vessel
        return out

    def get_current(self, origin: str, vessel: str) -> float:
        df = self.get_series(origin, vessel, days=30)
        return float(df["rate"].iloc[-1])

    def provenance(self) -> Dict[str, Any]:
        return {
            "source_type": "csv",
            "source_name": self.path,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "limitations": [
                "CSV provider — data quality depends on the supplied file",
                "Not a live commercial feed",
            ],
        }


class ExternalFreightProvider(FreightDataProvider):
    def get_series(self, origin: str, vessel: str, days: int = 540) -> pd.DataFrame:
        raise NotImplementedError(
            "ExternalFreightProvider is a future integration point. "
            "Configure FREIGHT_DATA_PROVIDER=synthetic for demo."
        )

    def get_current(self, origin: str, vessel: str) -> float:
        raise NotImplementedError("External live freight feed not configured.")

    def provenance(self) -> Dict[str, Any]:
        return {
            "source_type": "external_stub",
            "source_name": "ExternalFreightProvider",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "limitations": ["Not implemented — use synthetic for SIH demo"],
        }


def get_freight_provider() -> FreightDataProvider:
    name = get_settings().freight_data_provider.lower().strip()
    if name == "csv":
        return CSVFreightProvider()
    if name == "external":
        return ExternalFreightProvider()
    return SyntheticFreightProvider()


freight_provider = get_freight_provider()
