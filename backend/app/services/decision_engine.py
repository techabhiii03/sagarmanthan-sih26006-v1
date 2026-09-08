"""
Unified Decision Engine — orchestrates all modules into one coherent recommendation.
Every downstream module receives upstream outputs. Reason codes are machine-readable.
Supports freight_rate_override for full scenario pipeline re-runs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.ml.forecast_engine import forecast_engine
from app.services.port_engine import evaluate_pair
from app.services.vessel_optimizer import optimize_vessel
from app.services.voyage_engine import calculate_voyage
from app.services.market_entry import decide_entry
from app.services.contract_optimizer import optimize_contract
from app.services.idle_optimizer import optimize_idle
from app.services.risk_engine import assess_risk


def evaluate_requirement(
    origin: str,
    destination: str,
    cargo: str = "coking_coal",
    cargo_mt: float = 80000,
    laycan_start: Optional[str] = None,
    bunker_price: float = 520.0,
    extra_waiting_hrs: float = 0.0,
    risk_tolerance: str = "medium",
    num_voyages: int = 6,
    freight_rate_override: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Full pipeline:
    Forecast → Market Entry → Port Feasibility → Vessel Optimization →
    Voyage Economics → Contract Optimization → Idle Strategy → Risk → Final Decision

    freight_rate_override: when set (e.g. scenario shock), voyage/contract use this rate
    while forecast still provides trajectory for market-entry timing.
    """
    settings = get_settings()
    if cargo_mt < 0:
        return {
            "success": False,
            "decision": "AVOID",
            "error": {"code": "INVALID_CARGO", "message": "Cargo quantity cannot be negative"},
            "data_mode": settings.data_mode,
        }

    # 1. Vessel optimization (includes port feasibility)
    vessel_opt = optimize_vessel(
        origin, destination, cargo, cargo_mt, bunker_price, extra_waiting_hrs
    )
    recommended_vessel = vessel_opt.get("recommended")
    if not recommended_vessel:
        return {
            "decision": "AVOID",
            "decision_score": 0.9,
            "confidence": 0.9,
            "message": "No feasible vessel under current port constraints.",
            "vessel": vessel_opt,
            "reason_codes": ["NO_FEASIBLE_VESSEL", "PORT_CONSTRAINT_BLOCK"],
            "explanation": [
                vessel_opt.get("message", "Port constraints block all vessel classes.")
            ],
            "data_mode": settings.data_mode,
            "success": True,
        }

    # 2. Forecast for recommended vessel
    fc = forecast_engine.forecast(origin, recommended_vessel)
    effective_rate = float(
        freight_rate_override if freight_rate_override is not None else fc["current_rate"]
    )
    if freight_rate_override is not None:
        # Keep structure consistent for UI / market-entry awareness
        fc = dict(fc)
        fc["current_rate"] = round(effective_rate, 2)
        fc["scenario_rate_override"] = True

    # 3. Market entry (uses forecast trajectory)
    entry = decide_entry(origin, recommended_vessel, laycan_start, risk_tolerance)

    # 4. Voyage economics at effective rate (full multi-voyage program)
    voyage = calculate_voyage(
        origin,
        destination,
        recommended_vessel,
        cargo_mt,
        freight_rate_usd_mt=effective_rate,
        bunker_price_usd_mt=bunker_price,
        extra_waiting_hrs=extra_waiting_hrs,
    )
    if not voyage.get("success", True):
        return {
            "decision": "AVOID",
            "message": voyage.get("error", {}).get("message", "Voyage calculation failed"),
            "error": voyage.get("error"),
            "vessel": vessel_opt,
            "reason_codes": ["VOYAGE_CALC_FAILED"],
            "data_mode": settings.data_mode,
            "success": False,
        }

    # 5. Contract mix on full cargo program
    contract = optimize_contract(
        origin,
        recommended_vessel,
        cargo_mt,
        num_voyages,
        risk_tolerance,
        freight_rate_override=effective_rate,
    )

    # 6. Idle
    idle = optimize_idle(recommended_vessel, destination, bunker_price=bunker_price)

    # 7. Risk
    risk = assess_risk(
        origin, destination, recommended_vessel, cargo_mt, bunker_price, extra_waiting_hrs
    )

    # 8. Baseline vs optimized savings (no double-counting)
    # Baseline: 100% spot at current effective rate, same vessel program cost components
    # without contract discount and without timing benefit.
    baseline_freight = effective_rate * cargo_mt
    baseline_other = (
        voyage.get("bunker_cost_usd", 0)
        + voyage.get("port_charges_usd", 0)
        + voyage.get("waiting_cost_usd", 0)
        + voyage.get("handling_cost_usd", 0)
        + voyage.get("demurrage_cost_usd", 0)
        + voyage.get("deadhead_cost_usd", 0)
    )
    baseline_total = baseline_freight + baseline_other

    # Optimized: contract expected cost replaces pure spot freight component
    contract_cost = contract.get("expected_cost_usd", baseline_freight)
    optimized_total = contract_cost + baseline_other

    # Timing savings from market entry (only if WAIT has positive expected saving)
    timing_saving = max(0.0, float(entry.get("expected_saving_per_mt_usd", 0.0)) * cargo_mt)
    # Contract savings already = pure_spot_program - recommended_mix
    contract_saving = float(contract.get("projected_savings_vs_spot_usd", 0.0))
    # Vessel efficiency: already embodied in chosen vessel vs theoretical worst feasible
    ranked = vessel_opt.get("ranked_feasible") or []
    vessel_eff_saving = 0.0
    if len(ranked) >= 2:
        worst = max(ranked, key=lambda x: x.get("total_cost_usd") or 0)
        best_c = ranked[0].get("total_cost_usd") or 0
        worst_c = worst.get("total_cost_usd") or 0
        vessel_eff_saving = max(0.0, worst_c - best_c)

    idle_saving = max(0.0, float(idle.get("best_net_contribution_usd", 0) or 0))
    # Prefer positive idle benefit only
    if idle_saving < 0:
        idle_saving = 0.0

    # Total attributed without double-counting freight:
    # timing + contract are the primary savings levers on freight; vessel/idle are separate.
    total_saving_usd = timing_saving + contract_saving + vessel_eff_saving * 0.0 + idle_saving
    # vessel efficiency is informational (same vessel in baseline); set coefficient 0 to avoid double count
    total_saving_inr = total_saving_usd * settings.usd_inr_rate
    savings_pct = (total_saving_usd / baseline_total * 100) if baseline_total else 0.0

    # Final decision from entry, escalate if risk extreme or port infeasible
    final_decision = entry["decision"]
    reason_codes: List[str] = list(entry.get("reason_codes", []))
    if risk.get("overall", 0) > 78 and final_decision == "BOOK":
        final_decision = "WAIT"
        reason_codes.append("RISK_ESCALATION_TO_WAIT")
        entry.setdefault("reasons", []).append(
            "Overall risk elevated — deferred entry preferred."
        )
    if not vessel_opt.get("recommended"):
        final_decision = "AVOID"
        reason_codes.append("PORT_CONSTRAINT_BLOCK")

    reason_codes.append(f"VESSEL_{recommended_vessel.upper()}_LOWEST_PROGRAM_COST")
    reason_codes.append("PORT_FEASIBLE")
    reason_codes.append(
        f"CONTRACT_{contract['recommended'].upper().replace(' ', '_').replace('%', 'PCT').replace('/', '_')}"
    )
    reason_codes.append(f"IDLE_{idle['best_strategy']}")

    explanation: List[str] = []
    explanation.append(
        f"Selected vessel: {recommended_vessel} "
        f"({voyage.get('voyages_needed', 1)} voyage(s), "
        f"program cost ${voyage.get('total_voyage_cost_usd', 0):,.0f})."
    )
    for r in entry.get("reasons", []):
        explanation.append(r)
    if vessel_opt.get("selection_rationale"):
        explanation.extend(vessel_opt["selection_rationale"][1:])  # skip header
    explanation.append(
        f"Contract: {contract['recommended']} "
        f"(spot exposure {contract['spot_exposure']*100:.0f}%, "
        f"savings vs pure spot ${contract_saving:,.0f})."
    )
    explanation.append(
        f"Idle strategy: {idle.get('best_label', idle['best_strategy'])}."
    )
    explanation.append(f"Overall risk: {risk.get('level')} ({risk.get('overall')}/100).")
    if total_saving_usd > 0:
        explanation.append(
            f"Expected program savings ≈ ${total_saving_usd:,.0f} "
            f"(₹{total_saving_inr/1e5:.1f} lakh) vs pure-spot baseline."
        )

    port_summary = evaluate_pair(origin, destination, recommended_vessel, cargo)

    return {
        "success": True,
        "decision": final_decision,
        "decision_score": entry.get("decision_score", entry.get("confidence", 0.7)),
        "confidence": entry.get("decision_score", entry.get("confidence", 0.7)),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "input": {
            "origin": origin,
            "destination": destination,
            "cargo": cargo,
            "cargo_mt": cargo_mt,
            "bunker_price": bunker_price,
            "extra_waiting_hrs": extra_waiting_hrs,
            "risk_tolerance": risk_tolerance,
            "freight_rate_override": freight_rate_override,
        },
        "forecast": fc,
        "market_entry": entry,
        "vessel": vessel_opt,
        "voyage": voyage,
        "contract": contract,
        "idle": idle,
        "risk": risk,
        "ports": port_summary,
        "reason_codes": reason_codes,
        "explanation": explanation,
        "savings": {
            "baseline_total_cost_usd": round(baseline_total, 0),
            "optimized_total_cost_usd": round(optimized_total, 0),
            "total_savings_usd": round(total_saving_usd, 0),
            "total_savings_inr": round(total_saving_inr, 0),
            "savings_pct": round(savings_pct, 2),
            "components": {
                "timing_savings_usd": round(timing_saving, 0),
                "contract_savings_usd": round(contract_saving, 0),
                "vessel_efficiency_savings_usd": round(vessel_eff_saving, 0),
                "idle_avoidance_savings_usd": round(idle_saving, 0),
            },
            "note": (
                "Baseline = 100% spot at effective rate + same voyage non-freight costs. "
                "Vessel efficiency is informational (same vessel in baseline); "
                "not added into total to avoid double-counting."
            ),
            "fx_usd_inr": settings.usd_inr_rate,
        },
        "data_mode": settings.data_mode,
        "data_provenance": {
            "source_type": "synthetic_demo" if settings.demo_mode else settings.freight_data_provider,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "limitations": [
                "Freight series is synthetic demonstration data",
                "Route distances from prototype table",
                "Contract discounts are explicit DEMO assumptions",
            ],
        },
    }
