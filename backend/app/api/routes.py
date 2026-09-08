from fastapi import APIRouter, HTTPException
from typing import Any, Dict

from app.models.schemas import (
    ForecastRequest,
    VesselOptimizeRequest,
    PortCheckRequest,
    VoyageCostRequest,
    ContractRequest,
    IdleRequest,
    RiskRequest,
    DecisionRequest,
    ScenarioRequest,
)
from app.ml.forecast_engine import forecast_engine
from app.services.port_engine import evaluate_pair, check_vessel_at_port
from app.services.vessel_optimizer import optimize_vessel
from app.services.voyage_engine import calculate_voyage
from app.services.market_entry import decide_entry
from app.services.contract_optimizer import optimize_contract
from app.services.idle_optimizer import optimize_idle
from app.services.risk_engine import assess_risk
from app.services.decision_engine import evaluate_requirement
from app.data.ports import list_ports, get_port, PORTS
from app.data.vessels import list_vessels
from app.data.berths import list_berths, get_berth, best_berth_for_port

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "SagarManthan API", "version": "1.2.1-sih2026"}


@router.get("/ports")
def get_ports(type: str | None = None):
    return list_ports(type)


@router.get("/ports/{name}")
def get_port_detail(name: str):
    p = get_port(name)
    if not p:
        raise HTTPException(404, f"Port {name} not found")
    # attach berths for this port
    berths = list_berths(name)
    return {**p, "berths": berths}


@router.get("/vessels")
def get_vessels():
    return list_vessels()


@router.get("/berths")
def get_berths(port: str | None = None):
    return list_berths(port)


@router.get("/berths/{port}/best")
def get_best_berth(port: str):
    b = best_berth_for_port(port)
    if not b:
        raise HTTPException(404, f"No berth data for {port}")
    return b


@router.post("/forecast")
def api_forecast(req: ForecastRequest):
    try:
        return forecast_engine.forecast(req.origin, req.vessel, req.horizons)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/vessel/optimize")
def api_vessel(req: VesselOptimizeRequest):
    return optimize_vessel(
        req.origin, req.destination, req.cargo, req.cargo_mt, req.bunker_price, req.extra_waiting_hrs
    )


@router.post("/port/check")
def api_port(req: PortCheckRequest):
    return evaluate_pair(req.origin, req.destination, req.vessel, req.cargo)


@router.post("/voyage/cost")
def api_voyage(req: VoyageCostRequest):
    return calculate_voyage(
        req.origin,
        req.destination,
        req.vessel,
        req.cargo_mt,
        req.freight_rate,
        req.bunker_price,
        extra_waiting_hrs=req.extra_waiting_hrs,
    )


@router.post("/contract/optimize")
def api_contract(req: ContractRequest):
    return optimize_contract(
        req.origin, req.vessel, req.cargo_mt, req.num_voyages, req.risk_tolerance
    )


@router.post("/idle/optimize")
def api_idle(req: IdleRequest):
    return optimize_idle(req.vessel, req.current_port)


@router.post("/risk")
def api_risk(req: RiskRequest):
    return assess_risk(req.origin, req.destination, req.vessel, req.cargo_mt)


@router.post("/decision/evaluate")
def api_decision(req: DecisionRequest):
    """Main orchestration endpoint used by Decision Center."""
    try:
        return evaluate_requirement(
            origin=req.origin,
            destination=req.destination,
            cargo=req.cargo,
            cargo_mt=req.cargo_mt,
            laycan_start=req.laycan_start,
            bunker_price=req.bunker_price,
            extra_waiting_hrs=req.extra_waiting_hrs,
            risk_tolerance=req.risk_tolerance,
            num_voyages=req.num_voyages,
        )
    except Exception as e:
        raise HTTPException(500, f"Decision evaluation failed: {str(e)}")


@router.post("/scenario")
def api_scenario(req: ScenarioRequest):
    """What-if: apply shocks and re-run the COMPLETE decision pipeline twice.

    Architecture:
      Scenario Inputs → Modified market inputs → Full evaluate_requirement()
      (Forecast → Entry → Vessel → Port → Voyage → Contract → Idle → Risk → Decision)

    Freight shock is applied as freight_rate_override so voyage, contract,
    savings and decision all recompute — never a post-hoc display scale.
    """
    base = req.base
    cargo_mt = req.cargo_mt_override if req.cargo_mt_override is not None else base.cargo_mt
    dest = req.destination_override or base.destination
    origin = getattr(req, "origin_override", None) or base.origin
    bunker = base.bunker_price * (1 + req.bunker_pct_change / 100)
    waiting = base.extra_waiting_hrs + req.extra_waiting_hrs
    risk_tol = getattr(req, "risk_tolerance_override", None) or base.risk_tolerance

    # BASE run (no shocks other than shared identity)
    base_result = evaluate_requirement(
        origin=base.origin,
        destination=base.destination,
        cargo=base.cargo,
        cargo_mt=base.cargo_mt,
        laycan_start=base.laycan_start,
        bunker_price=base.bunker_price,
        extra_waiting_hrs=base.extra_waiting_hrs,
        risk_tolerance=base.risk_tolerance,
        num_voyages=base.num_voyages,
    )

    # Determine shocked freight rate from base forecast current_rate
    base_rate = None
    if base_result.get("forecast"):
        base_rate = base_result["forecast"].get("current_rate")
    if base_rate is None:
        base_rate = 18.0  # safe fallback only for missing forecast structure
    shocked_rate = round(base_rate * (1 + req.freight_pct_change / 100), 2)
    rate_override = shocked_rate if req.freight_pct_change != 0 else None

    scenario_result = evaluate_requirement(
        origin=origin,
        destination=dest,
        cargo=base.cargo,
        cargo_mt=cargo_mt,
        laycan_start=base.laycan_start,
        bunker_price=bunker,
        extra_waiting_hrs=waiting,
        risk_tolerance=risk_tol,
        num_voyages=base.num_voyages,
        freight_rate_override=rate_override,
    )

    def _snap(r: dict) -> dict:
        v = r.get("voyage") or {}
        vessel = r.get("vessel") or {}
        risk = r.get("risk") or {}
        sav = r.get("savings") or {}
        contract = r.get("contract") or {}
        idle = r.get("idle") or {}
        fc = r.get("forecast") or {}
        return {
            "decision": r.get("decision"),
            "freight_rate": fc.get("current_rate"),
            "forecast_14d": (fc.get("forecast") or fc.get("forecasts") or {}).get("forecast_14d"),
            "vessel": vessel.get("recommended"),
            "voyages_needed": v.get("voyages_needed"),
            "voyage_cost_usd": v.get("total_voyage_cost_usd"),
            "cost_per_mt": v.get("cost_per_mt_usd"),
            "contract_strategy": contract.get("recommended"),
            "idle_strategy": idle.get("best_strategy"),
            "risk_level": risk.get("level"),
            "risk_score": risk.get("overall"),
            "expected_savings_usd": sav.get("total_savings_usd"),
        }

    base_snap = _snap(base_result)
    scen_snap = _snap(scenario_result)

    comparison = {}
    for key in base_snap:
        b, s = base_snap[key], scen_snap[key]
        changed = b != s
        comparison[key] = {"base": b, "scenario": s, "changed": changed}

    scenario_result["base_snapshot"] = base_snap
    scenario_result["scenario_snapshot"] = scen_snap
    scenario_result["comparison"] = comparison
    scenario_result["scenario_applied"] = {
        "freight_pct_change": req.freight_pct_change,
        "bunker_pct_change": req.bunker_pct_change,
        "extra_waiting_hrs": req.extra_waiting_hrs,
        "cargo_mt_override": req.cargo_mt_override,
        "destination_override": req.destination_override,
        "origin_override": getattr(req, "origin_override", None),
        "freight_rate_base": base_rate,
        "freight_rate_shocked": shocked_rate if req.freight_pct_change != 0 else base_rate,
        "note": (
            "Complete pipeline re-executed under shocks. "
            "Freight shock applied via freight_rate_override into voyage, contract, savings, decision."
        ),
    }
    return scenario_result


@router.get("/model-card")
def model_card():
    """Model Card for judges — transparent documentation of the forecasting system."""
    return {
        "model_name": "SagarManthan Freight Forecast Ensemble",
        "models_evaluated": ["Naive", "MovingAverage", "SeasonalNaive", "XGBoost"],
        "selection_rule": "Lowest walk-forward MAPE (then RMSE)",
        "features": [
            "lag_1", "lag_3", "lag_7", "lag_14", "lag_30",
            "rolling_mean_7", "rolling_mean_14", "rolling_mean_30",
            "rolling_std_7", "rolling_std_14", "rolling_std_30",
            "day_of_week", "week_of_year", "month", "day_of_year", "trend",
        ],
        "validation": "Expanding-window walk-forward (step=7 days)",
        "metrics_reported": ["MAE", "RMSE", "MAPE", "sMAPE", "Directional Accuracy"],
        "horizons": [7, 14, 30, 60],
        "prediction_interval": {
            "method": "Residual quantile (empirical) scaled by sqrt(horizon)",
            "default_level": 0.80,
        },
        "dataset_type": "DEMONSTRATION / SYNTHETIC",
        "dataset_description": (
            "Synthetic daily freight series calibrated to realistic mid-2020s "
            "coal freight levels for Australia/Africa/Indonesia → East Coast India routes."
        ),
        "known_limitations": [
            "Series is synthetic; not licensed commercial freight data.",
            "No real-time AIS or live bunker feeds in demo mode.",
            "Recursive multi-step forecast accumulates error with horizon.",
            "Port limits are approximate public figures, not surveyed berth data.",
        ],
        "data_mode": "DEMO / SYNTHETIC",
        "last_updated": "2026-09-07",
    }
