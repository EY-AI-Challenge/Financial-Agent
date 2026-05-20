"""
models/lgbm_model.py — LightGBM direct multi-horizon forecaster.

Strategy: Direct forecasting
  - One model per horizon (5 / 21 / 252 days ahead)
  - Predicts log-return; converts back to price at inference
  - Quantile regression for confidence intervals (q10 / q90)
  - Walk-forward cross-validation to measure in-sample accuracy
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_percentage_error
import warnings
warnings.filterwarnings("ignore")


FEATURE_COLS: list[str] | None = None  # populated on first fit


def _get_feature_cols(df: pd.DataFrame, target_prefix: str = "target_") -> list[str]:
    exclude = {"Date", "Open", "High", "Low", "Close", "Volume"}
    exclude |= {c for c in df.columns if c.startswith(target_prefix)}
    return [c for c in df.columns if c not in exclude]


class LGBMForecaster:
    """
    Trains three LightGBM models (one per horizon) using direct forecasting.

    Parameters
    ----------
    horizons : dict, e.g. {"1w": 5, "1m": 21, "1y": 252}
    n_splits  : number of time-series CV folds for evaluation
    """

    def __init__(self, horizons: dict[str, int], n_splits: int = 5):
        self.horizons = horizons
        self.n_splits = n_splits
        self.models: dict[str, lgb.Booster] = {}
        self.lo_models: dict[str, lgb.Booster] = {}   # q10 lower bound
        self.hi_models: dict[str, lgb.Booster] = {}   # q90 upper bound
        self.feature_cols: list[str] = []
        self.cv_scores: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Shared LGB params
    # ------------------------------------------------------------------

    @staticmethod
    def _base_params(objective: str = "regression", alpha: float | None = None) -> dict:
        p = dict(
            boosting_type="gbdt",
            objective=objective,
            metric="mae",
            n_estimators=800,
            learning_rate=0.03,
            num_leaves=63,
            max_depth=7,
            min_child_samples=30,
            feature_fraction=0.7,
            bagging_fraction=0.8,
            bagging_freq=5,
            reg_alpha=0.1,
            reg_lambda=0.1,
            verbose=-1,
            n_jobs=-1,
        )
        if objective == "quantile" and alpha is not None:
            p["alpha"] = alpha
        return p

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------

    def fit(self, df: pd.DataFrame, verbose: bool = True) -> "LGBMForecaster":
        self.feature_cols = _get_feature_cols(df)

        for name, h in self.horizons.items():
            target_col = f"target_{name}"
            if target_col not in df.columns:
                raise ValueError(f"Target column '{target_col}' not found in df.")

            sub = df[self.feature_cols + [target_col]].dropna()
            X = sub[self.feature_cols].values
            y = sub[target_col].values

            if verbose:
                print(f"  [LGBM] Training horizon={name} ({h}d)  "
                      f"n_samples={len(X)}")

            # ----- CV evaluation ----------------------------------------
            tscv = TimeSeriesSplit(n_splits=self.n_splits)
            mapes: list[float] = []
            for train_idx, val_idx in tscv.split(X):
                model_cv = lgb.LGBMRegressor(**self._base_params())
                model_cv.fit(X[train_idx], y[train_idx],
                             eval_set=[(X[val_idx], y[val_idx])],
                             callbacks=[lgb.early_stopping(50, verbose=False)])
                pred_log = model_cv.predict(X[val_idx])
                # Convert log-return to price ratio for MAPE
                mapes.append(
                    mean_absolute_percentage_error(
                        np.exp(y[val_idx]), np.exp(pred_log)
                    )
                )
            self.cv_scores[name] = float(np.mean(mapes))
            if verbose:
                print(f"           CV MAPE = {self.cv_scores[name]:.4f}")

            # ----- Full fit (point + quantile) --------------------------
            ds = lgb.Dataset(X, label=y)

            # Point estimate
            self.models[name] = lgb.train(
                self._base_params(),
                ds,
                num_boost_round=800,
                valid_sets=[ds],
                callbacks=[lgb.log_evaluation(0)],
            )
            # Lower bound (q10)
            self.lo_models[name] = lgb.train(
                self._base_params("quantile", alpha=0.10),
                ds,
                num_boost_round=600,
                valid_sets=[ds],
                callbacks=[lgb.log_evaluation(0)],
            )
            # Upper bound (q90)
            self.hi_models[name] = lgb.train(
                self._base_params("quantile", alpha=0.90),
                ds,
                num_boost_round=600,
                valid_sets=[ds],
                callbacks=[lgb.log_evaluation(0)],
            )

        return self

    # ------------------------------------------------------------------
    # Predict
    # ------------------------------------------------------------------

    def predict(self, df: pd.DataFrame) -> dict[str, dict]:
        """
        Predict from the *last row* of df.

        Returns
        -------
        dict  {horizon_name: {"price": float, "low": float, "high": float,
                               "log_return": float, "cv_mape": float}}
        """
        last_row = df[self.feature_cols].iloc[[-1]]
        X_last = last_row.fillna(0).values
        current_price = float(df["Close"].iloc[-1])

        results: dict = {}
        for name in self.horizons:
            log_ret   = float(self.models[name].predict(X_last)[0])
            log_ret_lo = float(self.lo_models[name].predict(X_last)[0])
            log_ret_hi = float(self.hi_models[name].predict(X_last)[0])

            results[name] = {
                "price":      current_price * np.exp(log_ret),
                "low":        current_price * np.exp(log_ret_lo),
                "high":       current_price * np.exp(log_ret_hi),
                "log_return": log_ret,
                "cv_mape":    self.cv_scores.get(name, np.nan),
            }

        return results

    # ------------------------------------------------------------------
    # Feature importance
    # ------------------------------------------------------------------

    def feature_importance(self, horizon: str, top_n: int = 20) -> pd.DataFrame:
        if horizon not in self.models:
            raise ValueError(f"Model for horizon '{horizon}' not found.")
        imp = self.models[horizon].feature_importance(importance_type="gain")
        return (
            pd.DataFrame({"feature": self.feature_cols, "importance": imp})
            .sort_values("importance", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
