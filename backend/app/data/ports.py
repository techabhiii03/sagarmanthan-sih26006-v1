"""
Port Intelligence Dataset — East Coast India + major loading ports.
All values are DEMONSTRATION / SIMULATED based on publicly known approximate limits.
Source: Prototype Port Dataset | Updated: 2026-09-06
"""

from typing import Dict, Any, List

# Realistic approximate constraints for demonstration
PORTS: Dict[str, Dict[str, Any]] = {
    # ---------- Indian East Coast Discharge Ports ----------
    "Paradip": {
        "name": "Paradip",
        "country": "India",
        "type": "discharge",
        "lat": 20.2648,
        "lon": 86.6947,
        "max_draft_m": 16.5,
        "max_loa_m": 300.0,
        "max_beam_m": 45.0,
        "cargo_handling_mt_day": 45000,
        "berth_capacity": 4,
        "typical_waiting_hrs": 18,
        "congestion_index": 0.42,  # 0-1
        "compatible_cargo": ["coking_coal", "thermal_coal", "iron_ore", "limestone"],
        "notes": "Major SAIL discharge port. Draft limits Capesize fully laden.",
    },
    "Dhamra": {
        "name": "Dhamra",
        "country": "India",
        "type": "discharge",
        "lat": 20.8250,
        "lon": 87.0667,
        "max_draft_m": 18.0,
        "max_loa_m": 310.0,
        "max_beam_m": 48.0,
        "cargo_handling_mt_day": 50000,
        "berth_capacity": 3,
        "typical_waiting_hrs": 22,
        "congestion_index": 0.38,
        "compatible_cargo": ["coking_coal", "thermal_coal", "iron_ore"],
        "notes": "Deep draft capable. Preferred for larger vessels.",
    },
    "Visakhapatnam": {
        "name": "Visakhapatnam",
        "country": "India",
        "type": "discharge",
        "lat": 17.6868,
        "lon": 83.2185,
        "max_draft_m": 16.0,
        "max_loa_m": 280.0,
        "max_beam_m": 42.0,
        "cargo_handling_mt_day": 38000,
        "berth_capacity": 5,
        "typical_waiting_hrs": 28,
        "congestion_index": 0.55,
        "compatible_cargo": ["coking_coal", "thermal_coal", "iron_ore", "limestone"],
        "notes": "Busy multi-cargo port. Congestion risk higher.",
    },
    "Gangavaram": {
        "name": "Gangavaram",
        "country": "India",
        "type": "discharge",
        "lat": 17.6167,
        "lon": 83.2333,
        "max_draft_m": 18.5,
        "max_loa_m": 320.0,
        "max_beam_m": 50.0,
        "cargo_handling_mt_day": 55000,
        "berth_capacity": 2,
        "typical_waiting_hrs": 16,
        "congestion_index": 0.30,
        "compatible_cargo": ["coking_coal", "thermal_coal", "iron_ore"],
        "notes": "Private deep-water terminal. Excellent for Capesize.",
    },
    "Gopalpur": {
        "name": "Gopalpur",
        "country": "India",
        "type": "discharge",
        "lat": 19.2500,
        "lon": 84.9167,
        "max_draft_m": 14.0,
        "max_loa_m": 230.0,
        "max_beam_m": 35.0,
        "cargo_handling_mt_day": 25000,
        "berth_capacity": 2,
        "typical_waiting_hrs": 24,
        "congestion_index": 0.45,
        "compatible_cargo": ["thermal_coal", "iron_ore"],
        "notes": "Smaller draft. Handysize / Supramax preferred.",
    },
    "Haldia": {
        "name": "Haldia",
        "country": "India",
        "type": "discharge",
        "lat": 22.0333,
        "lon": 88.0667,
        "max_draft_m": 12.5,
        "max_loa_m": 225.0,
        "max_beam_m": 32.0,
        "cargo_handling_mt_day": 22000,
        "berth_capacity": 3,
        "typical_waiting_hrs": 36,
        "congestion_index": 0.62,
        "compatible_cargo": ["coking_coal", "thermal_coal"],
        "notes": "River port. Strict draft & LOA limits. Smaller vessels only.",
    },
    "Sagar-Sandheads": {
        "name": "Sagar-Sandheads",
        "country": "India",
        "type": "discharge",
        "lat": 21.6500,
        "lon": 88.0500,
        "max_draft_m": 13.5,
        "max_loa_m": 240.0,
        "max_beam_m": 36.0,
        "cargo_handling_mt_day": 20000,
        "berth_capacity": 1,
        "typical_waiting_hrs": 40,
        "congestion_index": 0.58,
        "compatible_cargo": ["thermal_coal"],
        "notes": "Anchorage / lighterage often required.",
    },
    # ---------- Loading Ports ----------
    "Newcastle": {
        "name": "Newcastle",
        "country": "Australia",
        "type": "loading",
        "lat": -32.9267,
        "lon": 151.7789,
        "max_draft_m": 16.5,
        "max_loa_m": 300.0,
        "max_beam_m": 50.0,
        "cargo_handling_mt_day": 60000,
        "berth_capacity": 6,
        "typical_waiting_hrs": 12,
        "congestion_index": 0.35,
        "compatible_cargo": ["coking_coal", "thermal_coal"],
        "notes": "Major Australian coal export hub.",
    },
    "Gladstone": {
        "name": "Gladstone",
        "country": "Australia",
        "type": "loading",
        "lat": -23.8489,
        "lon": 151.2594,
        "max_draft_m": 17.0,
        "max_loa_m": 310.0,
        "max_beam_m": 50.0,
        "cargo_handling_mt_day": 55000,
        "berth_capacity": 4,
        "typical_waiting_hrs": 15,
        "congestion_index": 0.40,
        "compatible_cargo": ["coking_coal", "thermal_coal"],
        "notes": "Queensland coal terminal.",
    },
    "Richards Bay": {
        "name": "Richards Bay",
        "country": "South Africa",
        "type": "loading",
        "lat": -28.7833,
        "lon": 32.0500,
        "max_draft_m": 19.0,
        "max_loa_m": 300.0,
        "max_beam_m": 48.0,
        "cargo_handling_mt_day": 70000,
        "berth_capacity": 5,
        "typical_waiting_hrs": 20,
        "congestion_index": 0.48,
        "compatible_cargo": ["thermal_coal"],
        "notes": "Key thermal coal origin (proxy for SA / Mozambique region).",
    },
    "Maputo": {
        "name": "Maputo",
        "country": "Mozambique",
        "type": "loading",
        "lat": -25.9653,
        "lon": 32.5892,
        "max_draft_m": 14.5,
        "max_loa_m": 250.0,
        "max_beam_m": 40.0,
        "cargo_handling_mt_day": 30000,
        "berth_capacity": 3,
        "typical_waiting_hrs": 30,
        "congestion_index": 0.52,
        "compatible_cargo": ["thermal_coal", "coking_coal"],
        "notes": "Mozambique coal export. Draft constraints apply.",
    },
    "Taboneo": {
        "name": "Taboneo",
        "country": "Indonesia",
        "type": "loading",
        "lat": -3.7000,
        "lon": 114.4000,
        "max_draft_m": 15.0,
        "max_loa_m": 280.0,
        "max_beam_m": 45.0,
        "cargo_handling_mt_day": 40000,
        "berth_capacity": 4,
        "typical_waiting_hrs": 18,
        "congestion_index": 0.45,
        "compatible_cargo": ["thermal_coal"],
        "notes": "Indonesian coal anchorage / terminal.",
    },
    "Hampton Roads": {
        "name": "Hampton Roads",
        "country": "USA",
        "type": "loading",
        "lat": 36.9500,
        "lon": -76.3000,
        "max_draft_m": 15.5,
        "max_loa_m": 300.0,
        "max_beam_m": 48.0,
        "cargo_handling_mt_day": 45000,
        "berth_capacity": 4,
        "typical_waiting_hrs": 14,
        "congestion_index": 0.33,
        "compatible_cargo": ["coking_coal", "thermal_coal"],
        "notes": "US East Coast coal export.",
    },
}

# Approximate great-circle distances (nm) for key routes — demonstration values
ROUTE_DISTANCES_NM: Dict[str, Dict[str, float]] = {
    "Newcastle": {
        "Paradip": 5200,
        "Dhamra": 5150,
        "Visakhapatnam": 5050,
        "Gangavaram": 5030,
        "Gopalpur": 5100,
        "Haldia": 5400,
        "Sagar-Sandheads": 5350,
    },
    "Gladstone": {
        "Paradip": 4800,
        "Dhamra": 4750,
        "Visakhapatnam": 4650,
        "Gangavaram": 4630,
        "Gopalpur": 4700,
        "Haldia": 5000,
        "Sagar-Sandheads": 4950,
    },
    "Richards Bay": {
        "Paradip": 4200,
        "Dhamra": 4150,
        "Visakhapatnam": 4050,
        "Gangavaram": 4030,
        "Gopalpur": 4100,
        "Haldia": 4400,
        "Sagar-Sandheads": 4350,
    },
    "Maputo": {
        "Paradip": 4500,
        "Dhamra": 4450,
        "Visakhapatnam": 4350,
        "Gangavaram": 4330,
        "Gopalpur": 4400,
        "Haldia": 4700,
        "Sagar-Sandheads": 4650,
    },
    "Taboneo": {
        "Paradip": 2800,
        "Dhamra": 2750,
        "Visakhapatnam": 2650,
        "Gangavaram": 2630,
        "Gopalpur": 2700,
        "Haldia": 3000,
        "Sagar-Sandheads": 2950,
    },
    "Hampton Roads": {
        "Paradip": 9800,
        "Dhamra": 9750,
        "Visakhapatnam": 9650,
        "Gangavaram": 9630,
        "Gopalpur": 9700,
        "Haldia": 10000,
        "Sagar-Sandheads": 9950,
    },
}

def get_port(name: str) -> Dict[str, Any] | None:
    return PORTS.get(name)

def list_ports(port_type: str | None = None) -> List[Dict[str, Any]]:
    if port_type:
        return [p for p in PORTS.values() if p["type"] == port_type]
    return list(PORTS.values())

def get_distance_nm(
    origin: str,
    destination: str,
    allow_estimated: bool = False,
) -> Dict[str, Any]:
    """
    Return route distance information.
    Never silently invent a distance.
    {
      "supported": bool,
      "distance_nm": float | None,
      "estimated": bool,
      "error": str | None
    }
    """
    table = ROUTE_DISTANCES_NM.get(origin, {})
    if destination in table:
        return {
            "supported": True,
            "distance_nm": float(table[destination]),
            "estimated": False,
            "error": None,
        }
    if allow_estimated:
        from app.core.config import get_settings
        est = get_settings().estimated_distance_nm
        return {
            "supported": True,
            "distance_nm": float(est),
            "estimated": True,
            "error": None,
        }
    return {
        "supported": False,
        "distance_nm": None,
        "estimated": False,
        "error": f"Route distance unavailable for {origin} → {destination}",
    }


def get_distance_nm_legacy(origin: str, destination: str) -> float:
    """Compatibility helper — raises if unsupported when estimation disabled."""
    info = get_distance_nm(origin, destination, allow_estimated=False)
    if not info["supported"] or info["distance_nm"] is None:
        raise ValueError(info["error"] or "Unsupported route")
    return float(info["distance_nm"])

