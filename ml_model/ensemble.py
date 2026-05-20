"""
models/ensemble.py — Weighted ensemble of LightGBM, Prophet, and Chronos.

Weighting strategy
------------------
  Short-term (1w / 1m):  LightGBM (0.55)  + Chronos (0.30) + Prophet (0.15)
  Long-term  (1y):       Prophet  (0.50)   + LightGBM (0.35) + Chronos (0.15)

Rationale
---------
  • LightGBM is strong at capturing recent market patterns via technical
    indicators; it dominates for short-term horizons.
  • Prophet models trend + seasonality explicitly; better for long-range.
  • Chronos provides a zero-shot prior from a model pre-trained on 27B
    time-series observations; acts as a regulariser / diversity booster.

When Chronos is unavailable its weight is redistributed proportionally to
the remaining models.

Confidence intervals
--------------------
  The final CI is the union (min-low, max-high) of all available model CIs,
  which tends to be well-calibrated in practice.
"""

from __future__ import annotations

import numpy as np


# Default weights per horizon
_WEIGHTS_SHORT = {"lgbm": 0.55, "prophet": 0.15, "chronos": 0.30}
_WEIGHTS_LONG  = {"lgbm": 0.35, "prophet": 0.50, "chronos": 0.15}

# Horizons considered "long" (use long weights)
_LONG_HORIZONS = {"1y"}


def _normalise(weights: dict[str, float], present_keys: set[str]) -> dict[str, float]:
    """Re-normalise after removing absent models."""
    w = {k: v for k, v in weights.items() if k in present_keys}
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}


def ensemble_predictions(
    lgbm_preds: dict | None,
    prophet_preds: dict | None,
    chronos_preds: dict | None,
    horizons: dict[str, int],
) -> dict[str, dict]:
    """
    Combine model predictions into a single ensemble forecast.

    Parameters
    ----------
    lgbm_preds    : output of LGBMForecaster.predict()   or None
    prophet_preds : output of ProphetForecaster.predict() or None
    chronos_preds : output of ChronosForecaster.predict() or None
    horizons      : dict mapping horizon name → trading days

    Returns
    -------
    dict  {
        horizon_name: {
            "price"      : float,  # ensemble point estimate
            "low"        : float,  # 10th-pct confidence bound
            "high"       : float,  # 90th-pct confidence bound
            "pct_change" : float,  # vs current close
            "sources"    : dict,   # per-model prices & weights
        }
    }
    """
    # Map model name → prediction dict
    model_preds = {
        "lgbm":    lgbm_preds,
        "prophet": prophet_preds,
        "chronos": chronos_preds,
    }
    # Only keep models that returned results
    available = {k for k, v in model_preds.items() if v is not None}

    results: dict = {}

    for name in horizons:
        base_weights = _WEIGHTS_LONG if name in _LONG_HORIZONS else _WEIGHTS_SHORT
        weights = _normalise(base_weights, available)

        prices: dict[str, float] = {}
        lows:   dict[str, float] = {}
        highs:  dict[str, float] = {}

        for model_name, w in weights.items():
            p = model_preds[model_name]
            if p is None or name not in p:
                continue
            prices[model_name] = p[name]["price"]
            lows[model_name]   = p[name]["low"]
            highs[model_name]  = p[name]["high"]

        if not prices:
            results[name] = None
            continue

        # Weighted point estimate (in log-price space for better averaging)
        log_prices    = {k: np.log(v) for k, v in prices.items()}
        ensemble_log  = sum(weights[k] * log_prices[k] for k in log_prices)
        ensemble_price = np.exp(ensemble_log)

        # CI: union of all model intervals (conservative but robust)
        ensemble_lo = min(lows.values())
        ensemble_hi = max(highs.values())

        # Retrieve current price from any available model's log_return
        # (we reconstruct from price / log_return)
        any_model = next(iter(available))
        current_price = (
            model_preds[any_model][name]["price"] /
            np.exp(model_preds[any_model][name]["log_return"])
        )

        results[name] = {
            "price":      float(ensemble_price),
            "low":        float(ensemble_lo),
            "high":       float(ensemble_hi),
            "pct_change": float((ensemble_price - current_price) / current_price * 100),
            "log_return": float(np.log(ensemble_price / current_price)),
            "current":    float(current_price),
            "sources": {
                k: {"price": prices[k], "weight": weights.get(k, 0)}
                for k in prices
            },
        }

    return results
