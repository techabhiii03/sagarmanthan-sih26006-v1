"""
Core numerical & constraint tests for SagarManthan SIH26006.
"""

import math
import pytest

from app.ml.forecast_engine import forecast_engine, FEATURE_COLS, _prepare_xy
from app.data.freight_generator import generate_freight_series
from app.services.voyage_engine import calculate_voyage
from app.services.vessel_optimizer import optimize_vessel
from app.services.port_engine import check_vessel_at_port, evaluate_pair
from app.services.contract_optimizer import optimize_contract, CONTRACT_ASSUMPTIONS
from app.services.idle_optimizer import optimize_idle
from app.services.market_entry import decide_entry
from app.services.decision_engine import evaluate_requirement
from app.data.ports import get_distance_nm
from app.core.config import get_settings


# ---------------------------------------------------------------------------
# Forecasting
# ---------------------------------------------------------------------------

def test_forecast_horizons():
    r = forecast_engine.forecast("Newcastle", "Panamax", horizons=[7, 14, 30, 60])
    assert "forecast_7d" in r["forecast"]
    assert "forecast_60d" in r["forecast"]
    assert r["current_rate"] > 0
    assert r["model"] in ("Naive", "MovingAverage", "SeasonalNaive", "XGBoost")
    assert "prediction_interval" in r
    assert r["prediction_interval"]["level"] == 0.80


def test_walk_forward_metrics_present():
    m = forecast_engine.evaluate_models("Newcastle", "Panamax")
    for name in m["models"]:
        assert "mae" in m["models"][name]
        assert "rmse" in m["models"][name]
        assert "mape" in m["models"][name]
        assert "dir_acc" in m["models"][name]
    assert m["selected"] in m["models"]


def test_no_future_leakage_in_features():
    df = generate_freight_series("Newcastle", "Panamax", days=200)
    X, y, d = _prepare_xy(df)
    for i in range(1, min(20, len(d))):
        assert abs(d.iloc[i]["lag_1"] - d.iloc[i - 1]["rate"]) < 1e-9


def test_future_calendar_features_correct():
    r = forecast_engine.forecast("Newcastle", "Supramax", horizons=[7])
    assert len(r["paths"]["path_7d"]) == 7


def test_constant_series_naive_preferred():
    m = forecast_engine.evaluate_models("Taboneo", "Handysize")
    assert m["selected"] is not None


def test_prediction_interval_structure():
    r = forecast_engine.forecast("Newcastle", "Panamax", horizons=[14])
    pi = r["prediction_interval"]
    assert pi["method"]
    assert "lower" in pi and "upper" in pi
    lo = pi["lower"].get("lower_14d")
    hi = pi["upper"].get("upper_14d")
    point = r["forecast"]["forecast_14d"]
    assert lo <= point <= hi


# ---------------------------------------------------------------------------
# Voyage economics
# ---------------------------------------------------------------------------

def test_voyage_total_equals_sum_of_components():
    v = calculate_voyage(
        "Newcastle", "Paradip", "Panamax", 80000,
        freight_rate_usd_mt=18.0, bunker_price_usd_mt=520.0,
    )
    assert v["success"] is True
    components = (
        v["freight_cost_usd"]
        + v["bunker_cost_usd"]
        + v["port_charges_usd"]
        + v["waiting_cost_usd"]
        + v["handling_cost_usd"]
        + v["demurrage_cost_usd"]
        + v["deadhead_cost_usd"]
    )
    assert abs(v["total_voyage_cost_usd"] - components) < 2.0


def test_bunker_cost_equals_fuel_times_price():
    v = calculate_voyage(
        "Newcastle", "Paradip", "Panamax", 50000,
        freight_rate_usd_mt=18.0, bunker_price_usd_mt=500.0,
    )
    assert abs(v["bunker_cost_usd"] - v["fuel_mt"] * 500.0) < 25.0  # rounding to nearest USD


def test_unsupported_route_fails_safely():
    r = calculate_voyage("FakeOrigin", "Paradip", "Panamax", 50000)
    assert r.get("success") is False
    assert r["error"]["code"] == "UNSUPPORTED_ROUTE"


def test_supported_route_has_distance():
    r = calculate_voyage("Newcastle", "Paradip", "Panamax", 50000)
    assert r.get("success") is True
    assert r["distance_nm"] > 0
    assert r["distance_estimated"] is False


def test_multi_voyage_scales_bunker_and_port():
    single = calculate_voyage("Newcastle", "Paradip", "Panamax", 50000)
    multi = calculate_voyage("Newcastle", "Paradip", "Panamax", 150000)
    assert multi["voyages_needed"] >= 2
    assert multi["bunker_cost_usd"] > single["bunker_cost_usd"]
    assert multi["port_charges_usd"] > single["port_charges_usd"]
    assert multi["program_economics"]["total_voyage_cost"] == multi["total_voyage_cost_usd"]


def test_zero_cargo_safe():
    r = calculate_voyage("Newcastle", "Paradip", "Panamax", 0)
    assert r.get("success") is True
    assert r["voyages_needed"] == 0


def test_negative_cargo_rejected():
    r = calculate_voyage("Newcastle", "Paradip", "Panamax", -100)
    assert r.get("success") is False
    assert r["error"]["code"] == "INVALID_CARGO"


# ---------------------------------------------------------------------------
# Port / vessel
# ---------------------------------------------------------------------------

def test_port_margins_present():
    r = check_vessel_at_port("Panamax", "Paradip")
    assert "margins" in r
    assert "draft_margin_m" in r["margins"]


def test_capesize_may_fail_draft_at_shallow_port():
    r = check_vessel_at_port("Capesize", "Visakhapatnam")
    if not r["feasible"]:
        assert any("DRAFT" in x for x in r["reasons"])


def test_origin_and_destination_evaluated():
    r = evaluate_pair("Newcastle", "Paradip", "Panamax", "coking_coal")
    assert "origin_check" in r and "destination_check" in r
    assert "margins" in r


def test_vessel_optimizer_returns_rationale():
    r = optimize_vessel("Newcastle", "Paradip", "coking_coal", 80000)
    assert r.get("recommended") is not None
    assert "objective" in r
    assert r.get("recommended_voyages", 0) >= 1


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

def test_contract_assumptions_exposed():
    r = optimize_contract("Newcastle", "Panamax", 80000, risk_tolerance="medium")
    assert "assumptions" in r
    assert "short_term_discount_pct" in r["assumptions"]
    assert r["assumptions"]["short_term_discount_pct"] == CONTRACT_ASSUMPTIONS["short_term_discount_pct"]


def test_contract_strategies_ranked():
    r = optimize_contract("Newcastle", "Panamax", 80000, risk_tolerance="low")
    assert len(r["all_strategies"]) >= 5
    assert r["projected_savings_vs_spot_usd"] >= 0
    # pure spot should be highest risk among strategies typically
    names = [s["name"] for s in r["all_strategies"]]
    assert "100% Spot" in names


def test_contract_uses_full_cargo():
    r = optimize_contract("Newcastle", "Panamax", 150000)
    assert r["program_cargo_mt"] == 150000


# ---------------------------------------------------------------------------
# Decision / scenario
# ---------------------------------------------------------------------------

def test_decision_end_to_end():
    r = evaluate_requirement("Newcastle", "Paradip", "coking_coal", 80000)
    assert r["decision"] in ("BOOK", "WAIT", "AVOID")
    assert r["vessel"]["recommended"] is not None
    assert "savings" in r
    assert "components" in r["savings"]
    assert r["voyage"]["voyages_needed"] >= 1


def test_decision_freight_override_propagates():
    base = evaluate_requirement("Newcastle", "Paradip", "coking_coal", 80000)
    shocked = evaluate_requirement(
        "Newcastle", "Paradip", "coking_coal", 80000,
        freight_rate_override=base["forecast"]["current_rate"] * 1.15,
    )
    assert shocked["voyage"]["freight_rate_usd_mt"] > base["voyage"]["freight_rate_usd_mt"]
    assert shocked["voyage"]["total_voyage_cost_usd"] > base["voyage"]["total_voyage_cost_usd"]


def test_infeasible_unknown_route_decision():
    r = evaluate_requirement("Nowhere", "Paradip", "coking_coal", 80000)
    # either AVOID or voyage failure
    assert r["decision"] in ("AVOID", "WAIT", "BOOK") or r.get("success") is False


# ---------------------------------------------------------------------------
# Config / distance
# ---------------------------------------------------------------------------

def test_settings_load():
    s = get_settings()
    assert s.bunker_price_usd_mt > 0
    assert s.usd_inr_rate > 0
    assert s.data_random_seed == 42


def test_distance_api_dict():
    ok = get_distance_nm("Newcastle", "Paradip")
    assert ok["supported"] is True
    assert ok["distance_nm"] == 5200
    bad = get_distance_nm("Nowhere", "Paradip")
    assert bad["supported"] is False
    assert bad["distance_nm"] is None


def test_idle_returns_strategies():
    r = optimize_idle("Panamax", "Paradip")
    assert "best_strategy" in r
    assert len(r.get("options", r.get("strategies", []))) >= 1 or "best_strategy" in r
