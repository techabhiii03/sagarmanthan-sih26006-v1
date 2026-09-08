"""
Voyage Economics Engine — transparent, multi-voyage aware cost calculation.

All assumptions are configurable via Settings and labelled in the response.
Never uses a silent fallback distance.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

from app.core.config import get_settings
from app.data.ports import get_distance_nm, get_port
from app.data.vessels import get_vessel
from app.data.freight_generator import get_current_rate


def calculate_voyage(
    origin: str,
    destination: str,
    vessel_name: str,
    cargo_mt: float,
    freight_rate_usd_mt: float | None = None,
    bunker_price_usd_mt: float | None = None,
    demurrage_usd_day: float | None = None,
    extra_waiting_hrs: float = 0.0,
    allow_estimated_distance: bool | None = None,
) -> Dict[str, Any]:
    settings = get_settings()
    if bunker_price_usd_mt is None:
        bunker_price_usd_mt = settings.bunker_price_usd_mt
    if allow_estimated_distance is None:
        allow_estimated_distance = settings.allow_estimated_distance

    vessel = get_vessel(vessel_name)
    if not vessel:
        return {
            "success": False,
            "error": {
                "code": "UNKNOWN_VESSEL",
                "message": f"Unknown vessel {vessel_name}",
            },
        }

    if cargo_mt < 0:
        return {
            "success": False,
            "error": {
                "code": "INVALID_CARGO",
                "message": "Cargo quantity cannot be negative",
            },
        }

    dist_info = get_distance_nm(origin, destination, allow_estimated=allow_estimated_distance)
    if not dist_info["supported"] or dist_info["distance_nm"] is None:
        return {
            "success": False,
            "error": {
                "code": "UNSUPPORTED_ROUTE",
                "message": dist_info.get("error")
                or f"No route distance available for {origin} → {destination}",
            },
            "distance": dist_info,
        }

    distance_nm = float(dist_info["distance_nm"])
    is_estimated = bool(dist_info.get("estimated"))

    # Capacity & voyages
    utilization = 0.95
    effective_capacity = vessel["typical_dwt"] * utilization
    if cargo_mt <= 0:
        voyages_needed = 0
        last_voyage_load = 0.0
    else:
        voyages_needed = max(1, math.ceil(cargo_mt / effective_capacity))
        last_voyage_load = cargo_mt - (voyages_needed - 1) * effective_capacity
        if last_voyage_load <= 0:
            last_voyage_load = min(cargo_mt, effective_capacity)

    speed = vessel["speed_kn"]
    sailing_days_oneway = distance_nm / (speed * 24.0)
    ballast_factor = settings.ballast_factor
    total_sailing_days_per_voyage = sailing_days_oneway * (1.0 + ballast_factor)

    laden_cons = vessel["laden_consumption_mt_day"]
    ballast_cons = vessel["ballast_consumption_mt_day"]
    fuel_per_voyage = (
        sailing_days_oneway * laden_cons
        + (sailing_days_oneway * ballast_factor) * ballast_cons
    )

    # Scale for multi-voyage (partial last voyage still incurs full sailing)
    total_fuel_mt = fuel_per_voyage * voyages_needed
    total_bunker_cost = total_fuel_mt * bunker_price_usd_mt

    if freight_rate_usd_mt is None:
        freight_rate_usd_mt = get_current_rate(origin, vessel_name)
    total_freight_cost = freight_rate_usd_mt * cargo_mt

    port_o = get_port(origin) or {}
    port_d = get_port(destination) or {}
    waiting_hrs_per_voyage = (
        port_o.get("typical_waiting_hrs", 15)
        + port_d.get("typical_waiting_hrs", 20)
        + extra_waiting_hrs
    )
    waiting_days_per_voyage = waiting_hrs_per_voyage / 24.0
    daily_hire = vessel["daily_hire_usd"]
    total_waiting_cost = waiting_days_per_voyage * daily_hire * voyages_needed

    handle_rate = min(
        port_o.get("cargo_handling_mt_day", 40000),
        port_d.get("cargo_handling_mt_day", 40000),
    )
    # Handling proportional to cargo, not voyages
    handling_days = (cargo_mt / max(handle_rate, 1)) * 2
    handling_cost = handling_days * daily_hire * settings.handling_hire_fraction

    port_charges_per_call = vessel["port_charges_usd"]
    total_port_cost = port_charges_per_call * 2 * voyages_needed  # both ends × voyages

    if demurrage_usd_day is None:
        demurrage_usd_day = daily_hire * 1.25
    cong = (
        port_o.get("congestion_index", 0.4) + port_d.get("congestion_index", 0.4)
    ) / 2
    demurrage_days_per_voyage = waiting_days_per_voyage * settings.demurrage_waiting_fraction * cong
    total_demurrage = demurrage_days_per_voyage * demurrage_usd_day * voyages_needed

    # Deadhead / positioning proxy — labelled estimate
    deadhead_per_voyage = distance_nm * settings.deadhead_cost_usd_per_nm
    total_deadhead = deadhead_per_voyage * voyages_needed

    # Hire for sailing time across all voyages
    total_hire_sailing = total_sailing_days_per_voyage * daily_hire * voyages_needed

    total_voyage_cost = (
        total_freight_cost
        + total_bunker_cost
        + total_port_cost
        + total_waiting_cost
        + handling_cost
        + total_demurrage
        + total_deadhead
    )
    cost_per_mt = total_voyage_cost / cargo_mt if cargo_mt > 0 else 0.0

    # Per-voyage snapshot (full load voyage)
    per_voyage = {
        "sailing_days": round(total_sailing_days_per_voyage, 2),
        "fuel_mt": round(fuel_per_voyage, 1),
        "bunker_cost_usd": round(fuel_per_voyage * bunker_price_usd_mt, 0),
        "port_charges_usd": round(port_charges_per_call * 2, 0),
        "waiting_cost_usd": round(waiting_days_per_voyage * daily_hire, 0),
        "deadhead_cost_usd": round(deadhead_per_voyage, 0),
        "load_mt": round(effective_capacity, 0),
    }

    return {
        "success": True,
        "origin": origin,
        "destination": destination,
        "vessel": vessel_name,
        "cargo_mt": cargo_mt,
        "distance_nm": round(distance_nm, 0),
        "distance_estimated": is_estimated,
        "distance_label": "ESTIMATED ROUTE" if is_estimated else "ROUTE TABLE",
        "sailing_days_oneway": round(sailing_days_oneway, 2),
        "total_sailing_days_approx": round(total_sailing_days_per_voyage * voyages_needed, 2),
        "fuel_mt": round(total_fuel_mt, 1),
        "bunker_price_usd_mt": bunker_price_usd_mt,
        "bunker_cost_usd": round(total_bunker_cost, 0),
        "freight_rate_usd_mt": round(freight_rate_usd_mt, 2),
        "freight_cost_usd": round(total_freight_cost, 0),
        "port_charges_usd": round(total_port_cost, 0),
        "waiting_hrs": round(waiting_hrs_per_voyage * voyages_needed, 1),
        "waiting_cost_usd": round(total_waiting_cost, 0),
        "handling_days": round(handling_days, 2),
        "handling_cost_usd": round(handling_cost, 0),
        "demurrage_cost_usd": round(total_demurrage, 0),
        "deadhead_cost_usd": round(total_deadhead, 0),
        "hire_sailing_cost_usd": round(total_hire_sailing, 0),
        "total_voyage_cost_usd": round(total_voyage_cost, 0),
        "cost_per_mt_usd": round(cost_per_mt, 2),
        "vessel_capacity_mt": round(effective_capacity, 0),
        "voyages_needed": voyages_needed,
        "last_voyage_load_mt": round(last_voyage_load, 0),
        "per_voyage": per_voyage,
        "program_economics": {
            "total_sailing_cost_proxy": round(total_hire_sailing, 0),
            "total_bunker_cost": round(total_bunker_cost, 0),
            "total_port_cost": round(total_port_cost, 0),
            "total_waiting_cost": round(total_waiting_cost, 0),
            "total_demurrage_proxy": round(total_demurrage, 0),
            "total_deadhead_cost": round(total_deadhead, 0),
            "total_freight_cost": round(total_freight_cost, 0),
            "total_voyage_cost": round(total_voyage_cost, 0),
            "total_cost_per_mt": round(cost_per_mt, 2),
        },
        "assumptions": {
            "ballast_factor": ballast_factor,
            "deadhead_cost_usd_per_nm": settings.deadhead_cost_usd_per_nm,
            "handling_hire_fraction": settings.handling_hire_fraction,
            "demurrage_waiting_fraction": settings.demurrage_waiting_fraction,
            "utilization": utilization,
            "bunker_price_source": "configured / request override",
        },
        "breakdown": {
            "freight_pct": round(total_freight_cost / total_voyage_cost * 100, 1)
            if total_voyage_cost
            else 0,
            "bunker_pct": round(total_bunker_cost / total_voyage_cost * 100, 1)
            if total_voyage_cost
            else 0,
            "port_pct": round(total_port_cost / total_voyage_cost * 100, 1)
            if total_voyage_cost
            else 0,
            "waiting_pct": round(total_waiting_cost / total_voyage_cost * 100, 1)
            if total_voyage_cost
            else 0,
            "other_pct": round(
                (handling_cost + total_demurrage + total_deadhead) / total_voyage_cost * 100, 1
            )
            if total_voyage_cost
            else 0,
        },
        "cost_components_detail": {
            "deadhead_cost": {
                "value": round(total_deadhead, 0),
                "method": "estimated_ballast_positioning_cost",
                "assumption": f"{settings.deadhead_cost_usd_per_nm} USD/NM × distance × voyages",
            },
            "demurrage_cost": {
                "value": round(total_demurrage, 0),
                "method": "congestion_weighted_waiting_proxy",
                "assumption": f"{settings.demurrage_waiting_fraction} × waiting × congestion × hire×1.25",
            },
            "handling_cost": {
                "value": round(handling_cost, 0),
                "method": "cargo_time × hire_fraction",
                "assumption": f"hire × {settings.handling_hire_fraction}",
            },
        },
        "fx": {
            "usd_inr_rate": settings.usd_inr_rate,
            "source": "Configured Demo Rate",
            "total_cost_inr": round(total_voyage_cost * settings.usd_inr_rate, 0),
            "cost_per_mt_inr": round(cost_per_mt * settings.usd_inr_rate, 2),
        },
        "data_provenance": {
            "bunker_model": "Fuel = sailing_days × daily_consumption (laden + ballast) × voyages",
            "distance_source": "Prototype route table (approx NM)"
            if not is_estimated
            else "Estimated (user-enabled fallback)",
            "note": "DEMONSTRATION CALCULATION — multi-voyage program economics",
            "multi_voyage": True,
        },
    }
