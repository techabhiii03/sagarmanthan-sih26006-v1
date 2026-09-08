"""
Berth-level constraint database — DEMONSTRATION / PROTOTYPE.
Merged from berth-level operational limits for East Coast terminals.
"""

from typing import Dict, Any, List, Optional

BERTHS: List[Dict[str, Any]] = [
    {
        "berth_key": "EQ-I (Paradip)",
        "display_name": "EQ-I",
        "port": "Paradip",
        "max_draft_m": 13.5,
        "max_loa_m": 225.0,
        "max_beam_m": 32.0,
        "max_dwt_approx": 65000,
        "waiting_hours_typical": 10,
        "notes": "Suitable for Handysize and smaller Supramax.",
    },
    {
        "berth_key": "EQ-II (Paradip)",
        "display_name": "EQ-II",
        "port": "Paradip",
        "max_draft_m": 15.0,
        "max_loa_m": 260.0,
        "max_beam_m": 40.0,
        "max_dwt_approx": 80000,
        "waiting_hours_typical": 12,
        "notes": "Suitable for full Supramax and Panamax.",
    },
    {
        "berth_key": "COT Berth (Paradip)",
        "display_name": "COT Berth",
        "port": "Paradip",
        "max_draft_m": 16.5,
        "max_loa_m": 300.0,
        "max_beam_m": 45.0,
        "max_dwt_approx": 90000,
        "waiting_hours_typical": 14,
        "notes": "Coal Import Terminal. Panamax OK. Capesize limited on draft/beam.",
    },
    {
        "berth_key": "Dhamra – Coal Berth",
        "display_name": "Dhamra Coal Berth",
        "port": "Dhamra",
        "max_draft_m": 17.5,
        "max_loa_m": 310.0,
        "max_beam_m": 50.0,
        "max_dwt_approx": 120000,
        "waiting_hours_typical": 8,
        "notes": "Larger Panamax and limited Capesize capability.",
    },
    {
        "berth_key": "Gangavaram – Deep Berth",
        "display_name": "Deep Berth",
        "port": "Gangavaram",
        "max_draft_m": 18.5,
        "max_loa_m": 320.0,
        "max_beam_m": 50.0,
        "max_dwt_approx": 180000,
        "waiting_hours_typical": 10,
        "notes": "Deep-water private terminal. Capesize feasible.",
    },
    {
        "berth_key": "Vizag – Coal Berth 1",
        "display_name": "Coal Berth 1",
        "port": "Visakhapatnam",
        "max_draft_m": 14.5,
        "max_loa_m": 250.0,
        "max_beam_m": 38.0,
        "max_dwt_approx": 75000,
        "waiting_hours_typical": 16,
        "notes": "Supramax and smaller Panamax.",
    },
    {
        "berth_key": "Gopalpur – Main",
        "display_name": "Main Berth",
        "port": "Gopalpur",
        "max_draft_m": 14.0,
        "max_loa_m": 230.0,
        "max_beam_m": 35.0,
        "max_dwt_approx": 55000,
        "waiting_hours_typical": 20,
        "notes": "Handysize / Supramax preferred.",
    },
    {
        "berth_key": "Haldia – Coal",
        "display_name": "Coal Berth",
        "port": "Haldia",
        "max_draft_m": 12.5,
        "max_loa_m": 225.0,
        "max_beam_m": 32.0,
        "max_dwt_approx": 45000,
        "waiting_hours_typical": 30,
        "notes": "River port. Strict limits. Smaller vessels only.",
    },
]


def list_berths(port: Optional[str] = None) -> List[Dict[str, Any]]:
    if port:
        return [b for b in BERTHS if b["port"].lower() == port.lower()]
    return list(BERTHS)


def get_berth(berth_key: str) -> Optional[Dict[str, Any]]:
    for b in BERTHS:
        if b["berth_key"] == berth_key:
            return b
    return None


def best_berth_for_port(port: str) -> Optional[Dict[str, Any]]:
    """Return berth with highest draft at port (most capable)."""
    candidates = list_berths(port)
    if not candidates:
        return None
    return max(candidates, key=lambda b: b["max_draft_m"])
