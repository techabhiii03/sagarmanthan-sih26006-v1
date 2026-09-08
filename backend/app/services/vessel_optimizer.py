"""
Vessel Type Optimization — minimize total program cost among feasible vessels.
Objective is explicit: total program cost + light risk penalty from port margins.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.data.vessels import list_vessels
from app.services.port_engine import evaluate_pair
from app.services.voyage_engine import calculate_voyage


def optimize_vessel(
    origin: str,
    destination: str,
    cargo: str,
    cargo_mt: float,
    bunker_price: float = 520.0,
    extra_waiting_hrs: float = 0.0,
) -> Dict[str, Any]:
    candidates: List[Dict[str, Any]] = []
    for v in list_vessels():
        name = v["name"]
        port_eval = evaluate_pair(origin, destination, name, cargo)
        if not port_eval["overall_feasible"]:
            candidates.append(
                {
                    "vessel": name,
                    "feasible": False,
                    "rejection_reasons": port_eval["rejection_reasons"],
                    "total_cost_usd": None,
                    "cost_per_mt": None,
                    "voyages_needed": None,
                    "port_margins": port_eval.get("margins"),
                    "score": None,
                }
            )
            continue

        voyage = calculate_voyage(
            origin,
            destination,
            name,
            cargo_mt,
            bunker_price_usd_mt=bunker_price,
            extra_waiting_hrs=extra_waiting_hrs,
        )
        if not voyage.get("success", True):
            candidates.append(
                {
                    "vessel": name,
                    "feasible": False,
                    "rejection_reasons": [
                        voyage.get("error", {}).get("message", "Voyage calculation failed")
                    ],
                    "total_cost_usd": None,
                    "cost_per_mt": None,
                    "voyages_needed": None,
                    "port_margins": port_eval.get("margins"),
                    "score": None,
                }
            )
            continue

        # Light risk penalty from tight draft/LOA/beam margins
        margins = port_eval.get("margins") or {}
        draft_m = margins.get("draft_margin_m")
        margin_penalty = 0.0
        if draft_m is not None and draft_m < 1.0:
            margin_penalty = (1.0 - draft_m) * 15000  # USD equivalent soft penalty

        total_cost = voyage["total_voyage_cost_usd"]
        score = total_cost + margin_penalty

        candidates.append(
            {
                "vessel": name,
                "feasible": True,
                "rejection_reasons": [],
                "total_cost_usd": total_cost,
                "cost_per_mt": voyage["cost_per_mt_usd"],
                "voyages_needed": voyage["voyages_needed"],
                "freight_rate": voyage["freight_rate_usd_mt"],
                "bunker_cost": voyage["bunker_cost_usd"],
                "waiting_cost": voyage["waiting_cost_usd"],
                "voyage_detail": voyage,
                "port_margins": margins,
                "margin_penalty_usd": round(margin_penalty, 0),
                "score": round(score, 0),
            }
        )

    feasible = [c for c in candidates if c["feasible"]]
    if not feasible:
        return {
            "recommended": None,
            "candidates": candidates,
            "message": "No vessel class is feasible under current port constraints.",
            "objective": "Minimize total program cost + port-margin risk penalty subject to origin & destination feasibility",
        }

    best = min(feasible, key=lambda x: x["score"])
    ranked = sorted(feasible, key=lambda x: x["score"])

    why = [
        f"{best['vessel']} selected because:",
        f"• fully feasible at both origin and destination",
        f"• requires {best['voyages_needed']} voyage(s) for {cargo_mt:,.0f} MT",
        f"• lowest total cargo-program cost (USD {best['total_cost_usd']:,.0f})",
        f"• cost/MT = USD {best['cost_per_mt']:.2f}",
    ]
    if best.get("port_margins"):
        dm = best["port_margins"].get("draft_margin_m")
        if dm is not None:
            why.append(f"• draft margin ≈ {dm:.1f} m")

    return {
        "recommended": best["vessel"],
        "recommended_cost_usd": best["total_cost_usd"],
        "recommended_cost_per_mt": best["cost_per_mt"],
        "recommended_voyages": best["voyages_needed"],
        "selection_rationale": why,
        "candidates": candidates,
        "ranked_feasible": [
            {
                "vessel": r["vessel"],
                "total_cost_usd": r["total_cost_usd"],
                "cost_per_mt": r["cost_per_mt"],
                "voyages_needed": r["voyages_needed"],
                "score": r["score"],
                "port_margins": r.get("port_margins"),
            }
            for r in ranked
        ],
        "objective": "Minimize total program cost (freight + bunker + port + waiting + demurrage + deadhead) + soft port-margin risk penalty, subject to origin & destination feasibility",
    }
