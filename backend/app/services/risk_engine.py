"""
Risk Engine — scores derived from forecast uncertainty, freight volatility,
bunker exposure, port congestion, vessel availability proxy and operational urgency.
Every score has an explainable calculation.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.data.ports import get_port
from app.data.vessels import get_vessel
from app.ml.forecast_engine import forecast_engine


def assess_risk(
    origin: str,
    destination: str,
    vessel: str,
    cargo_mt: float = 80000,
    bunker_price: float = 520.0,
    extra_waiting_hrs: float = 0.0,
) -> Dict[str, Any]:
    fc = forecast_engine.forecast(origin, vessel)
    metrics = fc["model_metrics"]
    current = fc["current_rate"]
    mape = metrics["mape"]
    rmse = metrics["rmse"]
    vol = rmse / max(current, 1.0)

    port_o = get_port(origin) or {}
    port_d = get_port(destination) or {}
    v = get_vessel(vessel) or {}

    # Component scores 0–100 (higher = more risk)
    freight_vol_score = min(100.0, vol * 400 + mape * 2.5)
    forecast_unc_score = min(
        100.0,
        mape * 3.5
        + (fc["upper_bounds"].get("upper_14d", current) - fc["lower_bounds"].get("lower_14d", current))
        / max(current, 1)
        * 120,
    )

    daily_cons = v.get("laden_consumption_mt_day", 30)
    bunker_exposure = (daily_cons * 25 * bunker_price) / max(current * cargo_mt, 1)
    bunker_score = min(100.0, bunker_exposure * 180 + 25)

    cong_o = port_o.get("congestion_index", 0.4)
    cong_d = port_d.get("congestion_index", 0.4)
    wait_hrs = (
        port_o.get("typical_waiting_hrs", 15)
        + port_d.get("typical_waiting_hrs", 20)
        + extra_waiting_hrs
    )
    congestion_score = min(100.0, (cong_o + cong_d) * 45 + wait_hrs * 0.6)

    dwt = v.get("typical_dwt", 80000)
    availability_score = min(100.0, 25 + (dwt / 200000) * 55)

    capacity = dwt * 0.95
    size_risk = 0.0 if cargo_mt <= capacity else min(40.0, (cargo_mt / capacity - 1) * 50)

    overall = (
        0.28 * freight_vol_score
        + 0.22 * forecast_unc_score
        + 0.15 * bunker_score
        + 0.18 * congestion_score
        + 0.10 * availability_score
        + 0.07 * size_risk
    )
    overall = round(min(100.0, max(0.0, overall)), 1)

    if overall >= 70:
        level = "HIGH"
    elif overall >= 45:
        level = "MEDIUM"
    else:
        level = "LOW"

    drivers: List[Dict[str, Any]] = [
        {"name": "Freight volatility", "score": round(freight_vol_score, 1), "weight": 0.28},
        {"name": "Forecast uncertainty", "score": round(forecast_unc_score, 1), "weight": 0.22},
        {"name": "Bunker exposure", "score": round(bunker_score, 1), "weight": 0.15},
        {"name": "Port congestion / waiting", "score": round(congestion_score, 1), "weight": 0.18},
        {"name": "Vessel availability", "score": round(availability_score, 1), "weight": 0.10},
        {"name": "Cargo vs capacity", "score": round(size_risk, 1), "weight": 0.07},
    ]
    drivers = sorted(drivers, key=lambda x: -x["score"])

    mitigations: List[str] = []
    if freight_vol_score > 55:
        mitigations.append("Increase multi-voyage cover to reduce spot exposure.")
    if forecast_unc_score > 55:
        mitigations.append("Shorten commitment horizon or wait for narrower prediction interval.")
    if bunker_score > 50:
        mitigations.append("Consider bunker price risk-sharing clause or fuel hedge.")
    if congestion_score > 55:
        mitigations.append("Prefer berths with lower typical waiting; add demurrage contingency.")
    if availability_score > 55:
        mitigations.append("Secure vessel earlier; consider adjacent size class as fallback.")
    if not mitigations:
        mitigations.append("Maintain balanced contract mix and monitor weekly forecast updates.")

    return {
        "overall": overall,
        "level": level,
        "category": level,
        "risk_score": overall,
        "drivers": drivers,
        "risk_drivers": [d["name"] for d in drivers[:3]],
        "mitigation_actions": mitigations,
        "components": {
            "freight_volatility": round(freight_vol_score, 1),
            "forecast_uncertainty": round(forecast_unc_score, 1),
            "bunker": round(bunker_score, 1),
            "congestion": round(congestion_score, 1),
            "vessel_availability": round(availability_score, 1),
        },
        "calculation": (
            "overall = 0.28*freight_vol + 0.22*forecast_unc + 0.15*bunker "
            "+ 0.18*congestion + 0.10*availability + 0.07*size_risk"
        ),
        "data_mode": "DEMO / SYNTHETIC",
        "data_provenance": "Derived from forecast metrics + port congestion indices + vessel parameters",
    }
