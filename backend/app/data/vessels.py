"""
Vessel class definitions — DEMONSTRATION DATA.
Typical dimensions and consumption based on industry averages.
"""

from typing import Dict, Any, List

VESSEL_CLASSES: Dict[str, Dict[str, Any]] = {
    "Handysize": {
        "name": "Handysize",
        "dwt_min": 25000,
        "dwt_max": 40000,
        "typical_dwt": 35000,
        "loa_m": 180.0,
        "beam_m": 28.0,
        "draft_laden_m": 10.5,
        "speed_kn": 13.5,
        "laden_consumption_mt_day": 22.0,
        "ballast_consumption_mt_day": 18.0,
        "port_charges_usd": 45000,
        "daily_hire_usd": 12000,
        "suitable_for": ["coking_coal", "thermal_coal", "iron_ore", "limestone"],
    },
    "Supramax": {
        "name": "Supramax",
        "dwt_min": 50000,
        "dwt_max": 60000,
        "typical_dwt": 58000,
        "loa_m": 200.0,
        "beam_m": 32.0,
        "draft_laden_m": 12.5,
        "speed_kn": 14.0,
        "laden_consumption_mt_day": 28.0,
        "ballast_consumption_mt_day": 23.0,
        "port_charges_usd": 55000,
        "daily_hire_usd": 14500,
        "suitable_for": ["coking_coal", "thermal_coal", "iron_ore"],
    },
    "Panamax": {
        "name": "Panamax",
        "dwt_min": 65000,
        "dwt_max": 82000,
        "typical_dwt": 76000,
        "loa_m": 225.0,
        "beam_m": 32.3,
        "draft_laden_m": 14.5,
        "speed_kn": 14.0,
        "laden_consumption_mt_day": 32.0,
        "ballast_consumption_mt_day": 26.0,
        "port_charges_usd": 70000,
        "daily_hire_usd": 16500,
        "suitable_for": ["coking_coal", "thermal_coal", "iron_ore"],
    },
    "Capesize": {
        "name": "Capesize",
        "dwt_min": 150000,
        "dwt_max": 180000,
        "typical_dwt": 170000,
        "loa_m": 290.0,
        "beam_m": 45.0,
        "draft_laden_m": 18.0,
        "speed_kn": 13.5,
        "laden_consumption_mt_day": 55.0,
        "ballast_consumption_mt_day": 45.0,
        "port_charges_usd": 110000,
        "daily_hire_usd": 22000,
        "suitable_for": ["coking_coal", "thermal_coal", "iron_ore"],
    },
}

def get_vessel(name: str) -> Dict[str, Any] | None:
    return VESSEL_CLASSES.get(name)

def list_vessels() -> List[Dict[str, Any]]:
    return list(VESSEL_CLASSES.values())
