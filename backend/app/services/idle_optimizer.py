"""
Idle & Positioning Optimizer — calculated comparison of WAIT / REPOSITION /
ALTERNATIVE EMPLOYMENT / DEADHEAD.
Numbers are derived from vessel parameters, distances and bunker price.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.data.ports import get_distance_nm
from app.data.vessels import get_vessel


def optimize_idle(
    vessel_name: str,
    current_port: str,
    next_cargo_origin: Optional[str] = None,
    daily_hire: Optional[float] = None,
    bunker_price: float = 520.0,
    expected_market_idle_days: float = 8.0,
) -> Dict[str, Any]:
    vessel = get_vessel(vessel_name)
    if not vessel:
        return {"error": "Unknown vessel"}

    hire = daily_hire or vessel["daily_hire_usd"]
    ballast_cons = vessel["ballast_consumption_mt_day"]
    speed = vessel["speed_kn"]

    options: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # A. WAIT at current port
    # ------------------------------------------------------------------
    wait_days = expected_market_idle_days
    wait_cost = wait_days * hire
    options.append(
        {
            "strategy": "WAIT",
            "label": "Wait at current port",
            "idle_days": round(wait_days, 1),
            "expected_revenue_usd": 0.0,
            "additional_cost_usd": round(wait_cost, 0),
            "fuel_cost_usd": 0.0,
            "net_contribution_usd": round(-wait_cost, 0),
            "deadhead_nm": 0.0,
            "description": "Stay idle until next fixture appears in current region.",
            "reason_codes": ["MARKET_IDLE_BASELINE"],
        }
    )

    # ------------------------------------------------------------------
    # B. REPOSITION to a liquid loading area
    # ------------------------------------------------------------------
    reposition_targets = {
        "Paradip": "Taboneo",
        "Dhamra": "Taboneo",
        "Visakhapatnam": "Taboneo",
        "Gangavaram": "Taboneo",
        "Gopalpur": "Taboneo",
        "Haldia": "Taboneo",
        "Newcastle": "Paradip",
        "Gladstone": "Paradip",
        "Richards Bay": "Paradip",
    }
    target = reposition_targets.get(current_port, "Taboneo")
    dist_info = get_distance_nm(current_port, target, allow_estimated=True)
    dist = float(dist_info["distance_nm"] or 1800.0)
    if dist <= 0:
        dist = 1800.0

    ballast_days = dist / (speed * 24.0)
    fuel_mt = ballast_days * ballast_cons
    fuel_cost = fuel_mt * bunker_price
    # partial hire during ballast (opportunity cost)
    hire_during_ballast = ballast_days * hire * 0.5
    idle_after_repo = 2.5
    total_repo_cost = fuel_cost + hire_during_ballast + idle_after_repo * hire
    options.append(
        {
            "strategy": "REPOSITION",
            "label": f"Reposition to {target}",
            "idle_days": round(idle_after_repo + ballast_days * 0.25, 1),
            "expected_revenue_usd": 0.0,
            "additional_cost_usd": round(total_repo_cost, 0),
            "fuel_cost_usd": round(fuel_cost, 0),
            "net_contribution_usd": round(-total_repo_cost, 0),
            "deadhead_nm": round(dist, 0),
            "description": f"Ballast toward {target} for higher fixture probability.",
            "reason_codes": ["REPOSITION_FOR_LIQUIDITY"],
        }
    )

    # ------------------------------------------------------------------
    # C. ALTERNATIVE EMPLOYMENT (short regional fixture)
    #    Contribution estimated from typical short-haul TCE margin
    #    relative to daily hire (not a hardcoded absolute).
    # ------------------------------------------------------------------
    # Assume a short fixture covers ~1.3× daily hire for 5 days after 1.5 idle days
    alt_idle = 1.5
    alt_employment_days = 5.0
    tce_multiple = 1.25  # modest positive TCE vs hire
    alt_revenue = alt_employment_days * hire * tce_multiple
    alt_cost = alt_idle * hire
    alt_net = alt_revenue - alt_cost
    options.append(
        {
            "strategy": "ALTERNATIVE_EMPLOYMENT",
            "label": "Alternative employment (short fixture)",
            "idle_days": round(alt_idle, 1),
            "expected_revenue_usd": round(alt_revenue, 0),
            "additional_cost_usd": round(alt_cost, 0),
            "fuel_cost_usd": 0.0,
            "net_contribution_usd": round(alt_net, 0),
            "deadhead_nm": 0.0,
            "description": "Accept short local/regional employment to cover hire and reduce idle.",
            "reason_codes": ["SHORT_FIXTURE_COVER"],
        }
    )

    # ------------------------------------------------------------------
    # D. DEADHEAD toward known next cargo origin (if supplied)
    # ------------------------------------------------------------------
    if next_cargo_origin and next_cargo_origin != current_port:
        dh_info = get_distance_nm(current_port, next_cargo_origin, allow_estimated=True)
        dh_dist = float(dh_info["distance_nm"] or 2200.0)
        dh_days = dh_dist / (speed * 24.0)
        dh_fuel = dh_days * ballast_cons * bunker_price
        dh_hire = dh_days * hire * 0.55
        dh_idle_after = 1.0
        dh_total = dh_fuel + dh_hire + dh_idle_after * hire
        options.append(
            {
                "strategy": "DEADHEAD",
                "label": f"Deadhead to {next_cargo_origin}",
                "idle_days": round(dh_idle_after + dh_days * 0.2, 1),
                "expected_revenue_usd": 0.0,
                "additional_cost_usd": round(dh_total, 0),
                "fuel_cost_usd": round(dh_fuel, 0),
                "net_contribution_usd": round(-dh_total, 0),
                "deadhead_nm": round(dh_dist, 0),
                "description": "Position empty for the next known requirement.",
                "reason_codes": ["DEADHEAD_TO_NEXT_CARGO"],
            }
        )
    else:
        # generic deadhead option with proxy distance
        dh_dist = 1600.0
        dh_days = dh_dist / (speed * 24.0)
        dh_fuel = dh_days * ballast_cons * bunker_price
        dh_hire = dh_days * hire * 0.55
        dh_total = dh_fuel + dh_hire + 2.0 * hire
        options.append(
            {
                "strategy": "DEADHEAD",
                "label": "Deadhead (generic positioning)",
                "idle_days": round(2.0 + dh_days * 0.2, 1),
                "expected_revenue_usd": 0.0,
                "additional_cost_usd": round(dh_total, 0),
                "fuel_cost_usd": round(dh_fuel, 0),
                "net_contribution_usd": round(-dh_total, 0),
                "deadhead_nm": round(dh_dist, 0),
                "description": "Ballast toward a higher-probability loading region.",
                "reason_codes": ["GENERIC_DEADHEAD"],
            }
        )

    # Rank by net contribution (descending)
    ranked = sorted(options, key=lambda o: o["net_contribution_usd"], reverse=True)
    best = ranked[0]
    baseline = options[0]["net_contribution_usd"]
    benefit = best["net_contribution_usd"] - baseline

    return {
        "current_expected_idle_days": expected_market_idle_days,
        "best_strategy": best["strategy"],
        "best_label": best["label"],
        "idle_reduced_to_days": best["idle_days"],
        "estimated_economic_benefit_usd": round(benefit, 0),
        "ranked": [
            {
                "rank": i + 1,
                "strategy": o["strategy"],
                "label": o["label"],
                "net_contribution_usd": o["net_contribution_usd"],
                "idle_days": o["idle_days"],
                "fuel_cost_usd": o["fuel_cost_usd"],
                "deadhead_nm": o["deadhead_nm"],
                "description": o["description"],
            }
            for i, o in enumerate(ranked)
        ],
        "options": options,
        "calculation_note": (
            "Net contribution = expected revenue − (idle hire + ballast fuel + opportunity cost). "
            "Alternative employment revenue derived from TCE multiple × daily hire (not a fixed constant)."
        ),
        "data_provenance": "DEMONSTRATION / Calculated from vessel parameters + distance table",
        "data_mode": "DEMO / SYNTHETIC",
    }
