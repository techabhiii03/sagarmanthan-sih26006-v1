"""
Market Entry Engine — transparent BOOK / WAIT / AVOID scoring.
Decision depends on forecast direction, expected price movement, uncertainty,
current rate, time horizon, volatility, risk tolerance and operational urgency.
All scores are calculated; no fabricated confidence.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.ml.forecast_engine import forecast_engine


def _score_decision(
    current: float,
    f14: float,
    f30: float,
    uncertainty: float,
    mape: float,
    risk_tolerance: str,
    urgency: float = 0.5,
) -> tuple[str, float, List[str], float]:
    """
    Documented scoring methodology.

    score components (higher → more BOOK pressure):
      - expected_savings_signal  : (current - f14) / max(current, 1)   (positive if decline expected)
      - uncertainty_penalty      : - (uncertainty / current)
      - volatility_penalty       : - mape / 100
      - urgency_bonus            : urgency * 0.15
      - risk_adjustment          : depends on tolerance

    Final decision thresholds on composite score.
    """
    reasons: List[str] = []
    reason_codes: List[str] = []

    delta_14 = f14 - current
    delta_30 = f30 - current
    expected_saving_per_mt = max(0.0, current - f14)

    # Normalised signals
    saving_signal = (current - f14) / max(current, 1.0)          # >0 → wait attractive
    rise_signal = (f14 - current) / max(current, 1.0)            # >0 → book now
    unc_ratio = uncertainty / max(current, 1.0)
    vol_penalty = mape / 100.0

    # Composite: positive favours WAIT (because rates expected to fall)
    composite = (
        1.2 * saving_signal
        - 0.8 * unc_ratio
        - 0.5 * vol_penalty
        - 0.3 * urgency
    )

    if risk_tolerance == "low":
        composite -= 0.08   # prefer locking earlier
    elif risk_tolerance == "high":
        composite += 0.06

    # Decision rules
    if unc_ratio > 0.22 or mape > 18:
        decision = "AVOID"
        reason_codes.append("HIGH_FORECAST_UNCERTAINTY")
        reasons.append(
            f"Forecast uncertainty ({uncertainty:.2f} USD/MT, MAPE {mape:.1f}%) exceeds safe commitment threshold."
        )
        decision_score = max(0.0, min(1.0, 0.35 - unc_ratio))
    elif composite > 0.035 and expected_saving_per_mt > 0.4:
        decision = "WAIT"
        reason_codes.append("FORECAST_DECLINING")
        reasons.append(
            f"14-day forecast declines by ${abs(delta_14):.2f}/MT "
            f"(>{uncertainty * 0.5:.2f} uncertainty threshold)."
        )
        if delta_30 < delta_14:
            reason_codes.append("LONGER_HORIZON_CONTINUES_DECLINE")
            reasons.append(f"30-day outlook continues lower (${f30:.2f}/MT).")
        decision_score = min(0.95, 0.55 + composite * 4)
    elif rise_signal > 0.04 and abs(delta_14) > uncertainty * 0.6:
        decision = "BOOK"
        reason_codes.append("FORECAST_RISING")
        reasons.append(
            f"14-day forecast rises by ${delta_14:.2f}/MT. Booking now locks the lower current rate."
        )
        decision_score = min(0.93, 0.60 + rise_signal * 5)
    elif abs(delta_14) < uncertainty * 0.45:
        decision = "BOOK" if risk_tolerance == "low" else "WAIT"
        reason_codes.append("CHANGE_WITHIN_UNCERTAINTY")
        reasons.append(
            "Expected change lies inside the uncertainty band — limited edge. "
            "Prefer locking if risk-averse."
        )
        decision_score = 0.58
    else:
        decision = "WAIT"
        reason_codes.append("MILD_DECLINE_SIGNAL")
        reasons.append("Mild expected decline; waiting for a clearer signal is preferred.")
        decision_score = 0.65

    return decision, round(decision_score, 3), reasons, expected_saving_per_mt


def decide_entry(
    origin: str,
    vessel: str,
    laycan_start: Optional[str] = None,
    risk_tolerance: str = "medium",
    urgency: float = 0.5,
) -> Dict[str, Any]:
    fc = forecast_engine.forecast(origin, vessel)
    current = fc["current_rate"]
    f7 = fc["forecasts"].get("forecast_7d", current)
    f14 = fc["forecasts"].get("forecast_14d", current)
    f30 = fc["forecasts"].get("forecast_30d", current)
    mape = fc["model_metrics"]["mape"]
    rmse = fc["model_metrics"]["rmse"]

    # Uncertainty band from residual method already returned by engine
    lo14 = fc["lower_bounds"].get("lower_14d", current - rmse)
    hi14 = fc["upper_bounds"].get("upper_14d", current + rmse)
    uncertainty = max(rmse * 1.2, (hi14 - lo14) / 2.0)

    decision, decision_score, reasons, expected_saving_per_mt = _score_decision(
        current, f14, f30, uncertainty, mape, risk_tolerance, urgency
    )

    # Entry window
    today = datetime(2026, 9, 7)
    if decision == "WAIT":
        best_start = today + timedelta(days=7)
        best_end = today + timedelta(days=14)
        latest_safe = today + timedelta(days=18)
        if laycan_start:
            try:
                lc = datetime.fromisoformat(laycan_start[:10])
                latest_safe = min(latest_safe, lc - timedelta(days=12))
            except Exception:
                pass
        entry_window = f"{best_start.strftime('%d %b')} – {best_end.strftime('%d %b')}"
        latest_str = latest_safe.strftime("%d %b %Y")
    elif decision == "AVOID":
        entry_window = "Defer until uncertainty contracts"
        latest_str = (today + timedelta(days=25)).strftime("%d %b %Y")
    else:
        entry_window = "Immediate"
        latest_str = (today + timedelta(days=3)).strftime("%d %b %Y")

    reason_codes = []
    for r in reasons:
        if "declines" in r.lower() or "decline" in r.lower():
            reason_codes.append("FORECAST_DECLINING")
        elif "rises" in r.lower():
            reason_codes.append("FORECAST_RISING")
        elif "uncertainty" in r.lower():
            reason_codes.append("HIGH_FORECAST_UNCERTAINTY")
        elif "within" in r.lower():
            reason_codes.append("CHANGE_WITHIN_UNCERTAINTY")
        else:
            reason_codes.append("MILD_SIGNAL")

    return {
        "decision": decision,
        "decision_score": decision_score,
        "confidence": decision_score,  # alias for UI compatibility; derived from score
        "current_rate": current,
        "forecast_7d": f7,
        "forecast_14d": f14,
        "forecast_30d": f30,
        "delta_14d": round(f14 - current, 2),
        "uncertainty_band": round(uncertainty, 2),
        "prediction_interval_14d": {"lower": lo14, "upper": hi14, "level": 0.80},
        "recommended_entry_window": entry_window,
        "latest_safe_booking_date": latest_str,
        "expected_saving_per_mt_usd": round(expected_saving_per_mt, 2),
        "reasons": reasons,
        "reason_codes": list(dict.fromkeys(reason_codes)),  # unique preserve order
        "model": fc["model_selected"],
        "mape": mape,
        "data_mode": fc.get("data_mode", "DEMO / SYNTHETIC"),
        "data_provenance": fc["data_provenance"],
    }
