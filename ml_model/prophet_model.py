"""
models/prophet_model.py — Facebook/Meta Prophet for trend + seasonality.

Prophet excels at:
  - Long-term trend modelling (log-scale price → linear trend)
  - Multiple seasonalities (weekly, monthly, annual)
  - Regime change detection via changepoints
  - Uncertainty intervals via Monte Carlo

We fit on log(Close) to model multiplicative growth, then exponentiate
predictions back to price space.
"""

from __future__ import annotations

import warnings
import numpy as np
import pandas as pd
import logging

# Suppress prophet / cmdstanpy noise
logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


class ProphetForecaster:
    """
    Wraps Prophet for multi-horizon stock price forecasting.

    Fits on log(Close) over a configurable recent window to avoid the
    model being dominated by decade-old price regimes.

    Parameters
    ----------
    horizons       : dict mapping name → trading-day horizon
    training_years : how many years of recent history to use for Prophet fit
    mcmc_samples   : >0 uses full MCMC for richer uncertainty; 0 = MAP (fast)
    """

    def __init__(
        self,
        horizons: dict[str, int],
        training_years: int = 5,
        mcmc_samples: int = 0,
    ):
        if not PROPHET_AVAILABLE:
            raise ImportError("prophet is not installed. Run: pip install prophet")
        self.horizons = horizons
        self.training_years = training_years
        self.mcmc_samples = mcmc_samples
        self.model: Prophet | None = None
        self.forecast_df: pd.DataFrame | None = None
        self._last_ds: pd.Timestamp | None = None

    # ------------------------------------------------------------------

    def fit(self, df: pd.DataFrame, verbose: bool = True) -> "ProphetForecaster":
        df = df[["Date", "Close"]].copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)

        # ---- Restrict to recent N years --------------------------------
        cutoff = df["Date"].max() - pd.DateOffset(years=self.training_years)
        df = df[df["Date"] >= cutoff].copy()
        self._last_ds = df["Date"].max()

        # ---- Log-transform target -------------------------------------
        prophet_df = pd.DataFrame({
            "ds": df["Date"],
            "y":  np.log(df["Close"]),
        })

        # ---- Build model -----------------------------------------------
        self.model = Prophet(
            growth="linear",
            changepoint_prior_scale=0.3,       # flexible trend
            seasonality_prior_scale=10.0,
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            mcmc_samples=self.mcmc_samples,
            interval_width=0.80,               # 80% CI
        )
        # Monthly seasonality (not built-in)
        self.model.add_seasonality(
            name="monthly", period=30.5, fourier_order=5
        )
        # Quarterly seasonality
        self.model.add_seasonality(
            name="quarterly", period=91.25, fourier_order=3
        )

        if verbose:
            print(f"  [Prophet] Fitting on {len(prophet_df)} rows "
                  f"(last {self.training_years} yrs)…")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(prophet_df)

        # ---- Pre-generate forecast far enough for 1y -------------------
        max_h = max(self.horizons.values())
        # trading days → calendar days (~1.4× buffer)
        calendar_days = int(max_h * 1.45) + 30
        future = self.model.make_future_dataframe(periods=calendar_days)
        self.forecast_df = self.model.predict(future)

        if verbose:
            print(f"  [Prophet] Done. Forecast horizon: {calendar_days} cal-days.")

        return self

    # ------------------------------------------------------------------

    def predict(self, df: pd.DataFrame) -> dict[str, dict]:
        """
        Returns price predictions for each horizon by counting trading days
        forward from the last date in df.
        """
        if self.model is None or self.forecast_df is None:
            raise RuntimeError("Call .fit() before .predict()")

        last_date = pd.to_datetime(df["Date"].max())
        current_price = float(df["Close"].iloc[-1])

        # Build a trading-day calendar from last_date
        trading_days = pd.bdate_range(
            start=last_date + pd.Timedelta(days=1),
            periods=max(self.horizons.values()) + 10,
        )

        results: dict = {}
        for name, h in self.horizons.items():
            target_date = trading_days[h - 1]

            # Find nearest forecast date
            fc = self.forecast_df.copy()
            fc["ds"] = pd.to_datetime(fc["ds"])
            idx = (fc["ds"] - target_date).abs().idxmin()
            row = fc.loc[idx]

            price     = np.exp(float(row["yhat"]))
            price_lo  = np.exp(float(row["yhat_lower"]))
            price_hi  = np.exp(float(row["yhat_upper"]))
            log_ret   = np.log(price / current_price)

            results[name] = {
                "price":      price,
                "low":        price_lo,
                "high":       price_hi,
                "log_return": log_ret,
                "target_date": str(target_date.date()),
            }

        return results

    # ------------------------------------------------------------------

    def components_df(self) -> pd.DataFrame | None:
        """Return the forecast DataFrame (includes trend, seasonalities)."""
        return self.forecast_df
