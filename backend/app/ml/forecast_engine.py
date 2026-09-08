"""
Freight Forecasting Engine — production-style pipeline for SIH26006.

Models: Naive, Moving Average, Seasonal Naive, XGBoost
- Full lag / rolling / calendar / trend feature set
- Genuine expanding-window walk-forward validation
- Residual-based prediction intervals
- Leakage-free recursive multi-horizon forecast with correct future calendar features
- Automatic best-model selection by MAPE (Naive may win)
All outputs labelled DEMONSTRATION DATA when synthetic series is used.
"""

from __future__ import annotations

import warnings
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")

from app.data.freight_generator import generate_freight_series, BASE_RATES


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def _mape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def _smape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.abs(y_true) + np.abs(y_pred)
    mask = denom != 0
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(2.0 * np.abs(y_pred[mask] - y_true[mask]) / denom[mask]) * 100)


def _directional_accuracy(y_true, y_pred, y_prev) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    y_prev = np.asarray(y_prev, dtype=float)
    true_dir = np.sign(y_true - y_prev)
    pred_dir = np.sign(y_pred - y_prev)
    return float(np.mean(true_dir == pred_dir) * 100)


# ---------------------------------------------------------------------------
# Feature engineering (no leakage)
# ---------------------------------------------------------------------------

FEATURE_COLS = [
    "lag_1", "lag_3", "lag_7", "lag_14", "lag_30",
    "rolling_mean_7", "rolling_mean_14", "rolling_mean_30",
    "rolling_std_7", "rolling_std_14", "rolling_std_30",
    "day_of_week", "week_of_year", "month", "day_of_year", "trend",
]


def _build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Create lag / rolling / calendar / trend features. Call only on historical data."""
    d = df.copy().reset_index(drop=True)
    d["date"] = pd.to_datetime(d["date"])
    d["day_of_week"] = d["date"].dt.dayofweek
    d["week_of_year"] = d["date"].dt.isocalendar().week.astype(int)
    d["month"] = d["date"].dt.month
    d["day_of_year"] = d["date"].dt.dayofyear
    d["trend"] = np.arange(len(d), dtype=float)

    d["lag_1"] = d["rate"].shift(1)
    d["lag_3"] = d["rate"].shift(3)
    d["lag_7"] = d["rate"].shift(7)
    d["lag_14"] = d["rate"].shift(14)
    d["lag_30"] = d["rate"].shift(30)

    d["rolling_mean_7"] = d["rate"].shift(1).rolling(7, min_periods=3).mean()
    d["rolling_mean_14"] = d["rate"].shift(1).rolling(14, min_periods=5).mean()
    d["rolling_mean_30"] = d["rate"].shift(1).rolling(30, min_periods=10).mean()
    d["rolling_std_7"] = d["rate"].shift(1).rolling(7, min_periods=3).std()
    d["rolling_std_14"] = d["rate"].shift(1).rolling(14, min_periods=5).std()
    d["rolling_std_30"] = d["rate"].shift(1).rolling(30, min_periods=10).std()

    return d


def _prepare_xy(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    d = _build_feature_frame(df)
    d = d.dropna(subset=FEATURE_COLS + ["rate"]).reset_index(drop=True)
    X = d[FEATURE_COLS]
    y = d["rate"]
    return X, y, d


# ---------------------------------------------------------------------------
# Forecast Engine
# ---------------------------------------------------------------------------

class ForecastEngine:
    def __init__(self):
        self.models_cache: Dict[str, Any] = {}
        self.metrics_cache: Dict[str, Dict] = {}
        self.residuals_cache: Dict[str, np.ndarray] = {}
        self.series_cache: Dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Walk-forward validation
    # ------------------------------------------------------------------
    def evaluate_models(
        self,
        origin: str,
        vessel: str,
        min_train: int = 180,
        step: int = 14,
    ) -> Dict[str, Any]:
        """
        Expanding-window walk-forward validation.
        Train on 1..t, predict t+1 (or block of `step` days), then expand.
        Computes MAE, RMSE, MAPE, sMAPE, directional accuracy for each model.
        """
        key = f"{origin}_{vessel}"
        if key in self.metrics_cache:
            return self.metrics_cache[key]

        df = generate_freight_series(origin, vessel, days=540)
        self.series_cache[key] = df
        X, y, d = _prepare_xy(df)

        if len(X) < min_train + 30:
            # fallback for short series
            min_train = max(60, len(X) // 2)

        n = len(X)
        origins = list(range(min_train, n - 1, step))
        if not origins:
            origins = [min_train]

        preds: Dict[str, List[float]] = {
            "Naive": [], "MovingAverage": [], "SeasonalNaive": [], "XGBoost": []
        }
        actuals: List[float] = []
        prevs: List[float] = []

        xgb_model = XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
            verbosity=0,
            n_jobs=1,
        )

        for t in origins:
            y_train = y.iloc[:t]
            X_train = X.iloc[:t]
            y_true = float(y.iloc[t])
            y_prev = float(y.iloc[t - 1])
            actuals.append(y_true)
            prevs.append(y_prev)

            # Naive
            preds["Naive"].append(float(y_train.iloc[-1]))

            # Moving Average 7
            preds["MovingAverage"].append(float(y_train.iloc[-7:].mean()))

            # Seasonal Naive (lag 7)
            if t >= 7:
                preds["SeasonalNaive"].append(float(y.iloc[t - 7]))
            else:
                preds["SeasonalNaive"].append(float(y_train.iloc[-1]))

            # XGBoost
            xgb_model.fit(X_train, y_train)
            p = float(xgb_model.predict(X.iloc[[t]])[0])
            preds["XGBoost"].append(p)

        results: Dict[str, Dict] = {}
        for name, pred_list in preds.items():
            if len(pred_list) == 0:
                continue
            yt = np.array(actuals)
            yp = np.array(pred_list)
            yp_prev = np.array(prevs)
            results[name] = {
                "mae": round(float(mean_absolute_error(yt, yp)), 3),
                "rmse": round(float(np.sqrt(mean_squared_error(yt, yp))), 3),
                "mape": round(_mape(yt, yp), 2),
                "smape": round(_smape(yt, yp), 2),
                "dir_acc": round(_directional_accuracy(yt, yp, yp_prev), 1),
                "n_folds": len(yt),
            }

        # Select best by MAPE (primary), then RMSE
        best_name = min(results.keys(), key=lambda k: (results[k]["mape"], results[k]["rmse"]))
        # Fit final XGB on full data for feature importance & residual distribution
        final_xgb = XGBRegressor(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
            verbosity=0,
            n_jobs=1,
        )
        final_xgb.fit(X, y)
        full_pred = final_xgb.predict(X)
        residuals = (y.values - full_pred).astype(float)

        self.models_cache[key] = {
            "xgb": final_xgb,
            "selected": best_name,
            "last_rate": float(y.iloc[-1]),
            "history_rates": y.values.tolist(),
            "last_date": d["date"].iloc[-1],
            "X_last": X.iloc[[-1]].copy(),
            "y_full": y,
            "d_full": d,
        }
        self.residuals_cache[key] = residuals

        fi = self._feature_importance(final_xgb, FEATURE_COLS)
        self.metrics_cache[key] = {
            "models": results,
            "selected": best_name,
            "selected_metrics": results[best_name],
            "feature_importance": fi,
            "validation": "Expanding-window walk-forward (step=14)",
            "n_observations": len(y),
        }
        return self.metrics_cache[key]

    def _feature_importance(self, model: XGBRegressor, feature_names: List[str]) -> Dict[str, float]:
        imp = model.feature_importances_
        total = float(imp.sum()) or 1.0
        return {name: round(float(v / total * 100), 1) for name, v in zip(feature_names, imp)}

    # ------------------------------------------------------------------
    # Residual-based prediction intervals
    # ------------------------------------------------------------------
    def _prediction_interval(
        self,
        point: float,
        residuals: np.ndarray,
        horizon: int,
        level: float = 0.80,
    ) -> Tuple[float, float]:
        """
        Empirical residual quantiles scaled by sqrt(horizon) for multi-step uncertainty.
        Practical method appropriate to the existing recursive architecture.
        """
        if residuals is None or len(residuals) < 10:
            band = abs(point) * 0.05 * (1 + 0.1 * np.sqrt(horizon))
            return round(point - band, 2), round(point + band, 2)

        alpha = (1.0 - level) / 2.0
        q_low = np.quantile(residuals, alpha)
        q_high = np.quantile(residuals, 1.0 - alpha)
        scale = np.sqrt(max(1.0, horizon))
        # dampen extreme scale growth
        scale = min(scale, 3.5)
        lower = point + q_low * scale
        upper = point + q_high * scale
        return round(float(lower), 2), round(float(upper), 2)

    # ------------------------------------------------------------------
    # Recursive multi-horizon forecast (no leakage)
    # ------------------------------------------------------------------
    def forecast(
        self,
        origin: str,
        vessel: str,
        horizons: List[int] = [7, 14, 30, 60],
        interval_level: float = 0.80,
    ) -> Dict[str, Any]:
        eval_res = self.evaluate_models(origin, vessel)
        key = f"{origin}_{vessel}"
        state = self.models_cache[key]
        residuals = self.residuals_cache.get(key, np.array([]))

        current_rate = state["last_rate"]
        last_date = pd.Timestamp(state["last_date"])
        history = list(state["history_rates"])
        selected = state["selected"]
        xgb = state["xgb"]

        # For selected model that is not XGB we still use XGB path for multi-step
        # when selected is a baseline we apply the baseline rule recursively.
        preds: Dict[str, float] = {}
        lowers: Dict[str, float] = {}
        uppers: Dict[str, float] = {}
        paths: Dict[str, List[float]] = {}
        change_pct: Dict[str, float] = {}

        max_h = max(horizons)
        # Build recursive path up to max_h
        rate_path: List[float] = []
        working_history = history.copy()

        for step in range(1, max_h + 1):
            future_date = last_date + timedelta(days=step)
            # calendar features for the actual future date
            dow = future_date.dayofweek
            woy = int(future_date.isocalendar()[1])
            month = future_date.month
            doy = future_date.dayofyear
            trend = len(working_history)

            # lags from working history (historical + previously predicted)
            def lag(k: int) -> float:
                if len(working_history) >= k:
                    return working_history[-k]
                return working_history[-1]

            lag1 = lag(1)
            lag3 = lag(3)
            lag7 = lag(7)
            lag14 = lag(14)
            lag30 = lag(30)

            def roll_mean(w: int) -> float:
                window = working_history[-w:] if len(working_history) >= w else working_history
                return float(np.mean(window))

            def roll_std(w: int) -> float:
                window = working_history[-w:] if len(working_history) >= w else working_history
                return float(np.std(window)) if len(window) > 1 else 0.0

            feat = {
                "lag_1": lag1,
                "lag_3": lag3,
                "lag_7": lag7,
                "lag_14": lag14,
                "lag_30": lag30,
                "rolling_mean_7": roll_mean(7),
                "rolling_mean_14": roll_mean(14),
                "rolling_mean_30": roll_mean(30),
                "rolling_std_7": roll_std(7),
                "rolling_std_14": roll_std(14),
                "rolling_std_30": roll_std(30),
                "day_of_week": dow,
                "week_of_year": woy,
                "month": month,
                "day_of_year": doy,
                "trend": float(trend),
            }
            X_step = pd.DataFrame([feat])[FEATURE_COLS]

            if selected == "Naive":
                p = lag1
            elif selected == "MovingAverage":
                p = roll_mean(7)
            elif selected == "SeasonalNaive":
                p = lag7
            else:  # XGBoost
                p = float(xgb.predict(X_step)[0])

            rate_path.append(p)
            working_history.append(p)

        for h in horizons:
            final_p = rate_path[h - 1]
            preds[f"forecast_{h}d"] = round(final_p, 2)
            lo, hi = self._prediction_interval(final_p, residuals, h, interval_level)
            lowers[f"lower_{h}d"] = lo
            uppers[f"upper_{h}d"] = hi
            paths[f"path_{h}d"] = [round(x, 2) for x in rate_path[:h]]
            change_pct[f"change_{h}d_pct"] = round(
                (final_p - current_rate) / current_rate * 100 if current_rate else 0.0, 2
            )

        # Direction from 14-day horizon
        f14 = preds.get("forecast_14d", current_rate)
        delta = f14 - current_rate
        if abs(delta) < current_rate * 0.01:
            direction = "STABLE"
        elif delta > 0:
            direction = "UP"
        else:
            direction = "DOWN"

        # Drivers
        fi = eval_res["feature_importance"]
        momentum = current_rate - (history[-8] if len(history) >= 8 else current_rate)
        drivers = []
        if momentum < -0.5:
            drivers.append("Recent freight momentum is negative (rate declined over last week).")
        elif momentum > 0.5:
            drivers.append("Recent freight momentum is positive (rate rose over last week).")
        top_feats = sorted(fi.items(), key=lambda x: -x[1])[:3]
        drivers.append(
            f"Top model drivers: {', '.join([f'{k} ({v}%)' for k, v in top_feats])}."
        )
        if fi.get("rolling_std_14", 0) > 12:
            drivers.append("Elevated short-term volatility is widening the forecast band.")

        return {
            "origin": origin,
            "vessel": vessel,
            "model": selected,
            "current_rate": round(current_rate, 2),
            "forecast": preds,
            "horizons": {str(h): preds.get(f"forecast_{h}d") for h in horizons},
            "forecast_change_pct": change_pct,
            "lower_bounds": lowers,
            "upper_bounds": uppers,
            "prediction_interval": {
                "level": interval_level,
                "method": "Residual quantile (empirical) scaled by sqrt(horizon)",
                "lower": lowers,
                "upper": uppers,
            },
            "direction": direction,
            "metrics": eval_res["selected_metrics"],
            "all_model_comparison": eval_res["models"],
            "feature_importance": fi,
            "explanation_drivers": drivers,
            "paths": paths,
            "data_mode": "DEMO / SYNTHETIC",
            "data_provenance": {
                "source": "DEMONSTRATION DATA / Synthetic series calibrated to realistic coal freight levels",
                "model_version": f"{selected} (walk-forward selected) + residual intervals",
                "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "validation": eval_res["validation"],
                "features": FEATURE_COLS,
                "interval_method": "Residual-based empirical quantiles",
            },
            # backward-compatible keys used by existing decision engine
            "forecasts": preds,
            "model_selected": selected,
            "model_metrics": eval_res["selected_metrics"],
        }


# singleton
forecast_engine = ForecastEngine()
