"""
Port Constraint Engine — explicit feasibility checks with reasons and safety margins.
Evaluates both origin (loading) and destination (discharge).
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.data.ports import get_port, list_ports
from app.data.vessels import get_vessel, list_vessels


def check_vessel_at_port(vessel_name: str, port_name: str) -> Dict[str, Any]:
    vessel = get_vessel(vessel_name)
    port = get_port(port_name)
    if not vessel or not port:
        return {
            "feasible": False,
            "reasons": [f"Unknown vessel or port: {vessel_name} / {port_name}"],
            "checks": {},
            "margins": {},
        }

    draft_req = vessel["draft_laden_m"]
    loa_req = vessel["loa_m"]
    beam_req = vessel["beam_m"]
    dwt = vessel.get("typical_dwt", 0)

    draft_lim = port["max_draft_m"]
    loa_lim = port["max_loa_m"]
    beam_lim = port["max_beam_m"]
    # ports may not have max_dwt; treat as soft if missing
    dwt_lim = port.get("max_dwt")

    draft_ok = draft_req <= draft_lim + 0.05
    loa_ok = loa_req <= loa_lim + 0.5
    beam_ok = beam_req <= beam_lim + 0.3
    dwt_ok = True if dwt_lim is None else dwt <= dwt_lim * 1.02

    checks = {
        "draft": {
            "required_m": draft_req,
            "port_limit_m": draft_lim,
            "ok": draft_ok,
            "shortfall_m": round(max(0.0, draft_req - draft_lim), 2),
        },
        "loa": {
            "required_m": loa_req,
            "port_limit_m": loa_lim,
            "ok": loa_ok,
            "shortfall_m": round(max(0.0, loa_req - loa_lim), 2),
        },
        "beam": {
            "required_m": beam_req,
            "port_limit_m": beam_lim,
            "ok": beam_ok,
            "shortfall_m": round(max(0.0, beam_req - beam_lim), 2),
        },
        "dwt": {
            "required_mt": dwt,
            "port_limit_mt": dwt_lim,
            "ok": dwt_ok,
        },
    }

    margins = {
        "draft_margin_m": round(draft_lim - draft_req, 2),
        "loa_margin_m": round(loa_lim - loa_req, 2),
        "beam_margin_m": round(beam_lim - beam_req, 2),
        "dwt_margin_mt": None if dwt_lim is None else round(dwt_lim - dwt, 0),
    }

    reasons: List[str] = []
    if not draft_ok:
        reasons.append(
            f"DRAFT violation: vessel draft {draft_req} m > port limit {draft_lim} m "
            f"(shortfall {checks['draft']['shortfall_m']} m)"
        )
    if not loa_ok:
        reasons.append(
            f"LOA violation: vessel LOA {loa_req} m > port limit {loa_lim} m"
        )
    if not beam_ok:
        reasons.append(
            f"BEAM violation: vessel beam {beam_req} m > port limit {beam_lim} m"
        )
    if not dwt_ok and dwt_lim is not None:
        reasons.append(
            f"DWT violation: vessel DWT {dwt} > port limit {dwt_lim}"
        )

    return {
        "vessel": vessel_name,
        "port": port_name,
        "feasible": len(reasons) == 0,
        "checks": checks,
        "margins": margins,
        "reasons": reasons if reasons else ["All physical constraints satisfied"],
        "port_congestion": port["congestion_index"],
        "typical_waiting_hrs": port["typical_waiting_hrs"],
        "cargo_handling_mt_day": port["cargo_handling_mt_day"],
    }


def evaluate_pair(
    origin: str, destination: str, vessel_name: str, cargo: str
) -> Dict[str, Any]:
    origin_check = check_vessel_at_port(vessel_name, origin)
    dest_check = check_vessel_at_port(vessel_name, destination)
    vessel = get_vessel(vessel_name)
    port_d = get_port(destination)

    cargo_ok = True
    cargo_reasons: List[str] = []
    if vessel and cargo not in vessel.get("suitable_for", []):
        cargo_ok = False
        cargo_reasons.append(f"Vessel class not typically used for {cargo}")
    if port_d and cargo not in port_d.get("compatible_cargo", []):
        cargo_ok = False
        cargo_reasons.append(f"Destination port does not commonly handle {cargo}")

    overall = origin_check["feasible"] and dest_check["feasible"] and cargo_ok
    reasons: List[str] = []
    if not origin_check["feasible"]:
        reasons.extend([f"ORIGIN ({origin}): {r}" for r in origin_check["reasons"]])
    if not dest_check["feasible"]:
        reasons.extend([f"DESTINATION ({destination}): {r}" for r in dest_check["reasons"]])
    reasons.extend(cargo_reasons)

    # Combined margins (tightest)
    o_m = origin_check.get("margins") or {}
    d_m = dest_check.get("margins") or {}
    combined_margins = {
        "draft_margin_m": min(
            o_m.get("draft_margin_m", 99), d_m.get("draft_margin_m", 99)
        ),
        "loa_margin_m": min(o_m.get("loa_margin_m", 99), d_m.get("loa_margin_m", 99)),
        "beam_margin_m": min(
            o_m.get("beam_margin_m", 99), d_m.get("beam_margin_m", 99)
        ),
        "origin": o_m,
        "destination": d_m,
    }

    return {
        "origin_check": origin_check,
        "destination_check": dest_check,
        "cargo_compatible": cargo_ok,
        "overall_feasible": overall,
        "rejection_reasons": reasons if not overall else ["Feasible at both ends"],
        "waiting_hrs_origin": origin_check.get("typical_waiting_hrs", 0),
        "waiting_hrs_destination": dest_check.get("typical_waiting_hrs", 0),
        "congestion_origin": origin_check.get("port_congestion", 0),
        "congestion_destination": dest_check.get("port_congestion", 0),
        "margins": combined_margins,
    }
