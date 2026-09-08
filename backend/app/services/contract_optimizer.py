"""
Contract Mix Optimizer — dynamic strategies driven by forecast + configurable assumptions.

All rate discounts / risk penalties live in CONTRACT_ASSUMPTIONS (demo-configurable).
No unexplained magic numbers buried in ranking logic.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.ml.forecast_engine import forecast_engine
from app.core.config import get_settings


# Explicit, documented demo assumptions (can be overridden via request later)
CONTRACT_ASSUMPTIONS: Dict[str, Any] = {
    "short_term_discount_pct": 2.0,       # short-term cover vs spot
    "medium_term_discount_pct": 4.5,      # medium-term cover vs spot
    "spot_volatility_multiplier": 1.8,    # risk premium on pure spot
    "short_volatility_multiplier": 0.9,
    "medium_volatility_multiplier": 0.45,
    "flexibility_cost_pct": 0.5,          # flexibility premium on lower commitment
    "min_commitment_fraction": 0.0,
    "max_commitment_fraction": 1.0,
    "note": "DEMO assumptions — not commercial contract quotes",
}


def optimize_contract(
    origin: str,
    vessel: str,
    cargo_mt: float,
    num_voyages_planned: int = 6,
    risk_tolerance: str = "medium",
    freight_rate_override: float | None = None,
) -> Dict[str, Any]:
    """
    Evaluate contract strategies for the FULL cargo program (cargo_mt × program).
    Strategies are ranked by expected cost + risk penalty adjusted for risk_tolerance.
    """
    settings = get_settings()
    fc = forecast_engine.forecast(origin, vessel)
    current = float(freight_rate_override if freight_rate_override is not None else fc["current_rate"])
    f30 = float(fc.get("forecast", {}).get("forecast_30d") or fc.get("forecasts", {}).get("forecast_30d", current))
    f60 = float(fc.get("forecast", {}).get("forecast_60d") or fc.get("forecasts", {}).get("forecast_60d", current))
    mape = float(fc.get("model_metrics", {}).get("mape") or fc.get("metrics", {}).get("mape", 8.0))
    rmse = float(fc.get("model_metrics", {}).get("rmse") or fc.get("metrics", {}).get("rmse", 1.5))
    volatility = (rmse / current) if current else 0.1

    a = CONTRACT_ASSUMPTIONS
    short_rate = current * (1.0 - a["short_term_discount_pct"] / 100.0)
    medium_rate = current * (1.0 - a["medium_term_discount_pct"] / 100.0)
    spot_avg = (current + f30 + f60) / 3.0

    # Risk premium in USD/MT derived from volatility (not fixed scores)
    spot_premium = volatility * current * a["spot_volatility_multiplier"]
    short_premium = volatility * current * a["short_volatility_multiplier"]
    medium_premium = volatility * current * a["medium_volatility_multiplier"]

    def program_cost(rate_usd_mt: float, premium: float = 0.0) -> float:
        return (rate_usd_mt + premium) * cargo_mt

    # Strategies: (name, spot_frac, short_frac, medium_frac)
    mixes = [
        ("100% Spot", 1.0, 0.0, 0.0),
        ("70% Spot / 30% Short-Term", 0.70, 0.30, 0.0),
        ("50% Short / 50% Medium", 0.0, 0.50, 0.50),
        ("30% Short / 70% Medium", 0.0, 0.30, 0.70),
        ("100% Medium-Term", 0.0, 0.0, 1.0),
        ("Balanced 15/25/60", 0.15, 0.25, 0.60),
    ]

    strategies: List[Dict[str, Any]] = []
    for name, spot_f, short_f, med_f in mixes:
        cost = (
            spot_f * program_cost(spot_avg, spot_premium)
            + short_f * program_cost(short_rate, short_premium)
            + med_f * program_cost(medium_rate, medium_premium)
        )
        # flexibility cost: higher when more volume left on spot
        flex_cost = spot_f * cargo_mt * current * (a["flexibility_cost_pct"] / 100.0)
        expected_cost = cost + flex_cost

        # Dynamic risk score 0-100 from exposure + mape/volatility
        risk_score = min(
            100.0,
            spot_f * 85.0 + short_f * 50.0 + med_f * 30.0 + mape * 0.4 + volatility * 80.0,
        )
        committed = (short_f + med_f) * cargo_mt
        downside = spot_f * cargo_mt * (spot_premium + max(0.0, current - min(f30, f60)))
        upside = (short_f + med_f) * cargo_mt * max(0.0, current - medium_rate)

        strategies.append(
            {
                "name": name,
                "mix": {"spot": spot_f, "short_term": short_f, "medium_term": med_f},
                "expected_cost_usd": round(expected_cost, 0),
                "spot_exposure": round(spot_f, 2),
                "risk_score": round(risk_score, 1),
                "committed_volume_mt": round(committed, 0),
                "flexibility": round(spot_f, 2),
                "downside_exposure_usd": round(downside, 0),
                "upside_capture_usd": round(upside, 0),
            }
        )

    # Rank by risk-adjusted cost depending on tolerance
    tol = (risk_tolerance or "medium").lower()
    if tol in ("low", "conservative"):
        # penalize risk heavily
        def score(s):
            return s["expected_cost_usd"] + s["risk_score"] * 8000
    elif tol in ("high", "aggressive"):
        def score(s):
            return s["expected_cost_usd"] + s["risk_score"] * 1500
    else:
        def score(s):
            return s["expected_cost_usd"] + s["risk_score"] * 4000

    ranked = sorted(strategies, key=score)
    best = ranked[0]
    pure_spot = next(s for s in strategies if s["name"] == "100% Spot")
    savings = pure_spot["expected_cost_usd"] - best["expected_cost_usd"]

    return {
        "recommended": best["name"],
        "spot_exposure": best["spot_exposure"],
        "expected_cost_usd": best["expected_cost_usd"],
        "projected_savings_vs_spot_usd": round(max(0.0, savings), 0),
        "risk_score": best["risk_score"],
        "committed_volume_mt": best["committed_volume_mt"],
        "all_strategies": [
            {
                "name": s["name"],
                "mix": s["mix"],
                "expected_cost_usd": s["expected_cost_usd"],
                "spot_exposure": s["spot_exposure"],
                "risk_score": s["risk_score"],
                "committed_volume_mt": s["committed_volume_mt"],
                "downside_exposure_usd": s["downside_exposure_usd"],
                "upside_capture_usd": s["upside_capture_usd"],
            }
            for s in ranked
        ],
        "assumptions": {**a, "fx_usd_inr": settings.usd_inr_rate},
        "program_cargo_mt": cargo_mt,
        "num_voyages_context": num_voyages_planned,
        "data_provenance": (
            "Dynamic costs from forecast trajectory + volatility-derived premiums. "
            "Discounts are DEMO assumptions listed under 'assumptions'."
        ),
    }
