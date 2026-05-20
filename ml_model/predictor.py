"""
predictor.py — StockPredictor: end-to-end pipeline orchestrator.

Usage
-----
    from predictor import StockPredictor

    sp = StockPredictor(ticker="AAPL", use_chronos=True)
    sp.load_data("AAPL.csv")
    sp.train(verbose=True)
    result = sp.predict()
    sp.print_summary(result)
    sp.plot(result, save_path="AAPL_forecast.png")
"""

from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

# Ensure this file's directory is on sys.path so sibling .py files
# are always importable regardless of where the calling script lives.
sys.path.insert(0, str(Path(__file__).parent))

from features import build_features, make_targets
from lgbm_model import LGBMForecaster
from prophet_model import ProphetForecaster
from chronos_model import ChronosForecaster
from ensemble import ensemble_predictions


HORIZONS = {"1w": 5, "1m": 21, "1y": 252}   # trading days


class StockPredictor:
    """
    Full pipeline: data → features → model training → ensemble prediction.

    Parameters
    ----------
    ticker         : ticker symbol (used only for display / plot titles)
    use_chronos    : attempt to load Amazon Chronos foundation model
    chronos_size   : model size for Chronos ("tiny"|"mini"|"small"|"base"|"large")
    prophet_years  : how many years of history to give Prophet (default 5)
    n_cv_splits    : time-series CV folds for LightGBM evaluation
    """

    def __init__(
        self,
        ticker: str = "STOCK",
        use_chronos: bool = True,
        chronos_size: str = "small",
        prophet_years: int = 5,
        n_cv_splits: int = 5,
    ):
        self.ticker = ticker.upper()
        self.use_chronos = use_chronos
        self.chronos_size = chronos_size
        self.prophet_years = prophet_years
        self.n_cv_splits = n_cv_splits

        self.raw_df: pd.DataFrame | None = None
        self.feat_df: pd.DataFrame | None = None

        self.lgbm: LGBMForecaster | None = None
        self.prophet: ProphetForecaster | None = None
        self.chronos: ChronosForecaster | None = None

        self._trained = False

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_data(self, path: str | Path) -> "StockPredictor":
        """
        Load OHLCV CSV.

        Expected columns: Date, Close, High, Low, Open, Volume
        (column order does not matter).
        """
        df = pd.read_csv(path)
        df.columns = [c.strip().title() for c in df.columns]
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        df = df.dropna(subset=["Close"])

        # Sanity checks
        required = {"Date", "Open", "High", "Low", "Close", "Volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing columns: {missing}")

        self.raw_df = df
        print(f"[{self.ticker}] Loaded {len(df):,} rows  "
              f"({df['Date'].min().date()} → {df['Date'].max().date()})")
        return self

    def load_dataframe(self, df: pd.DataFrame) -> "StockPredictor":
        """Alternative: pass a DataFrame directly."""
        self.raw_df = df.copy()
        return self

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, verbose: bool = True) -> "StockPredictor":
        if self.raw_df is None:
            raise RuntimeError("Call load_data() first.")

        t0 = time.time()
        print(f"\n{'='*60}")
        print(f"  Training pipeline for {self.ticker}")
        print(f"{'='*60}")

        # ---- Feature engineering ----------------------------------------
        if verbose:
            print("\n[1/4] Engineering features…")
        feat_df = build_features(self.raw_df)
        feat_df = make_targets(feat_df, HORIZONS)
        # Drop warm-up rows (NaN features) and look-ahead rows (NaN targets)
        feat_df = feat_df.dropna(subset=list(feat_df.columns)).reset_index(drop=True)
        self.feat_df = feat_df

        if verbose:
            print(f"      {len(feat_df):,} usable rows, "
                  f"{len(feat_df.columns)} columns "
                  f"({sum(1 for c in feat_df.columns if not c.startswith(('target_', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume')))} feature cols)")

        # ---- LightGBM ---------------------------------------------------
        if verbose:
            print("\n[2/4] Training LightGBM (direct multi-horizon)…")
        self.lgbm = LGBMForecaster(HORIZONS, n_splits=self.n_cv_splits)
        self.lgbm.fit(feat_df, verbose=verbose)

        # ---- Prophet ----------------------------------------------------
        if verbose:
            print("\n[3/4] Fitting Prophet (trend + seasonality)…")
        self.prophet = ProphetForecaster(HORIZONS, training_years=self.prophet_years)
        self.prophet.fit(self.raw_df, verbose=verbose)

        # ---- Chronos (optional) ----------------------------------------
        if verbose:
            print("\n[4/4] Loading Chronos pre-trained foundation model…")
        self.chronos = ChronosForecaster(model_size=self.chronos_size)
        self.chronos.load(device="cpu", verbose=verbose)

        self._trained = True
        elapsed = time.time() - t0
        print(f"\n✓ Training complete in {elapsed:.1f}s")
        return self

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self) -> dict[str, dict]:
        """
        Run all models on the most recent data and return an ensemble
        forecast for each horizon.

        Returns
        -------
        dict  {horizon: {price, low, high, pct_change, sources, …}}
        """
        if not self._trained:
            raise RuntimeError("Call train() before predict().")

        # We build features on the FULL raw data (no target rows dropped)
        # so we always have features for the very last trading day.
        full_feat = build_features(self.raw_df)

        lgbm_preds    = self.lgbm.predict(full_feat)
        prophet_preds = self.prophet.predict(self.raw_df)
        chronos_preds = (
            self.chronos.predict(self.raw_df, HORIZONS)
            if (self.chronos and self.chronos.available and self.chronos.pipeline)
            else None
        )

        ensemble = ensemble_predictions(
            lgbm_preds, prophet_preds, chronos_preds, HORIZONS
        )

        # Attach per-model CV scores for display
        for name in HORIZONS:
            if ensemble.get(name):
                ensemble[name]["lgbm_cv_mape"] = self.lgbm.cv_scores.get(name, None)

        return ensemble

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    @staticmethod
    def print_summary(results: dict, ticker: str = "") -> None:
        header = f" {ticker} Forecast Summary " if ticker else " Forecast Summary "
        print(f"\n{'='*60}")
        print(f"{header.center(60)}")
        print(f"{'='*60}")

        current = None
        for name, data in results.items():
            if data and current is None:
                current = data["current"]
                print(f"  Current price  : ${current:.2f}\n")
            if data is None:
                print(f"  {name.upper():6s}  ⚠  No prediction available")
                continue

            sign = "▲" if data["pct_change"] >= 0 else "▼"
            print(
                f"  {name.upper():6s}  {sign} ${data['price']:>9.2f}  "
                f"({data['pct_change']:+.1f}%)   "
                f"CI: [${data['low']:.2f}, ${data['high']:.2f}]"
            )
            if data.get("sources"):
                for model, s in data["sources"].items():
                    print(f"          ↳ {model:8s} ${s['price']:>9.2f}  "
                          f"(w={s['weight']:.2f})")
            if data.get("lgbm_cv_mape") is not None:
                print(f"          LightGBM CV MAPE: {data['lgbm_cv_mape']:.2%}")
            print()

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------

    def plot(
        self,
        results: dict,
        save_path: str | Path | None = None,
        history_days: int = 500,
    ) -> None:
        """
        Generate a 2×2 figure:
          [0,0]  Full price history + last N days zoom
          [0,1]  Forecast fan chart (CI bands)
          [1,0]  Feature importance (LightGBM, 1-week model)
          [1,1]  Per-model comparison bar chart
        """
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import matplotlib.patches as mpatches

        HORIZON_LABELS = {"1w": "1 Week", "1m": "1 Month", "1y": "1 Year"}
        COLORS = {"1w": "#3498db", "1m": "#e67e22", "1y": "#2ecc71"}

        fig, axes = plt.subplots(2, 2, figsize=(18, 12))
        fig.patch.set_facecolor("#0f0f0f")
        for ax in axes.flat:
            ax.set_facecolor("#1a1a2e")
            ax.tick_params(colors="#cccccc")
            ax.xaxis.label.set_color("#cccccc")
            ax.yaxis.label.set_color("#cccccc")
            ax.title.set_color("#ffffff")
            for spine in ax.spines.values():
                spine.set_edgecolor("#333355")

        df = self.raw_df.copy()
        df["Date"] = pd.to_datetime(df["Date"])

        last_date = df["Date"].max()
        current_price = float(df["Close"].iloc[-1])

        # ── [0,0] Recent price history ──────────────────────────────────
        ax = axes[0, 0]
        hist = df.tail(history_days)
        ax.plot(hist["Date"], hist["Close"], color="#7ec8e3", linewidth=1.2,
                label="Close price")
        ax.set_title(f"{self.ticker} — Last {history_days} Trading Days",
                     fontsize=13, fontweight="bold")
        ax.set_ylabel("Price ($)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
        ax.legend(framealpha=0.3, labelcolor="#cccccc",
                  facecolor="#1a1a2e", edgecolor="#333355")

        # ── [0,1] Forecast fan chart ─────────────────────────────────────
        ax = axes[0, 1]
        # Plot recent 60 days as context
        hist60 = df.tail(60)
        ax.plot(hist60["Date"], hist60["Close"], color="#7ec8e3", linewidth=1.4,
                label="Recent close", zorder=5)
        ax.axhline(current_price, color="#7ec8e3", linestyle=":", linewidth=0.8,
                   alpha=0.5)

        from pandas.tseries.offsets import BDay
        for name, data in results.items():
            if data is None:
                continue
            h_days = HORIZONS[name]
            target_date = last_date + h_days * BDay()
            color = COLORS[name]
            # Point
            ax.scatter(target_date, data["price"], color=color, s=80,
                       zorder=10, label=f"{HORIZON_LABELS[name]}: "
                                        f"${data['price']:.2f} "
                                        f"({data['pct_change']:+.1f}%)")
            # Line to point
            ax.plot([last_date, target_date],
                    [current_price, data["price"]],
                    color=color, linewidth=1.5, linestyle="--", alpha=0.8)
            # CI band
            ax.fill_between(
                [last_date, target_date],
                [current_price, data["low"]],
                [current_price, data["high"]],
                alpha=0.12, color=color,
            )
            # Annotate
            ax.annotate(
                f"${data['price']:.2f}",
                xy=(target_date, data["price"]),
                xytext=(5, 8), textcoords="offset points",
                color=color, fontsize=9, fontweight="bold",
            )

        ax.set_title(f"{self.ticker} — Price Forecast", fontsize=13, fontweight="bold")
        ax.set_ylabel("Price ($)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
        ax.legend(framealpha=0.3, labelcolor="#cccccc",
                  facecolor="#1a1a2e", edgecolor="#333355", fontsize=9)

        # ── [1,0] Feature importance (LightGBM 1w) ──────────────────────
        ax = axes[1, 0]
        try:
            imp_df = self.lgbm.feature_importance("1w", top_n=15)
            bars = ax.barh(imp_df["feature"][::-1], imp_df["importance"][::-1],
                           color="#7ec8e3", edgecolor="#0f0f0f", height=0.7)
            ax.set_title("Top Features — LightGBM (1-Week Model)",
                         fontsize=12, fontweight="bold")
            ax.set_xlabel("Feature Importance (gain)")
        except Exception:
            ax.text(0.5, 0.5, "Feature importance unavailable",
                    ha="center", va="center", transform=ax.transAxes,
                    color="#cccccc")

        # ── [1,1] Per-model comparison ────────────────────────────────────
        ax = axes[1, 1]
        model_names = []
        prices_1w, prices_1m, prices_1y = [], [], []

        for name, data in results.items():
            if data and data.get("sources"):
                for model, s in data["sources"].items():
                    if model not in model_names:
                        model_names.append(model)

        horizon_data = {h: {} for h in HORIZONS}
        for name, data in results.items():
            if data and data.get("sources"):
                for model, s in data["sources"].items():
                    horizon_data[name][model] = s["price"]

        if model_names:
            x = np.arange(len(model_names))
            width = 0.25
            offsets = [-width, 0, width]
            horizon_keys = list(HORIZONS.keys())
            for i, (hname, color) in enumerate(COLORS.items()):
                vals = [
                    horizon_data[hname].get(m, np.nan) for m in model_names
                ]
                bars = ax.bar(x + offsets[i], vals, width,
                              label=HORIZON_LABELS[hname],
                              color=color, alpha=0.85, edgecolor="#0f0f0f")
                for bar, v in zip(bars, vals):
                    if not np.isnan(v):
                        ax.text(bar.get_x() + bar.get_width() / 2,
                                bar.get_height() + 0.5,
                                f"${v:.0f}", ha="center", va="bottom",
                                fontsize=8, color=color)

            ax.axhline(current_price, color="#ffffff", linestyle=":",
                       linewidth=1, alpha=0.6, label=f"Current ${current_price:.2f}")
            ax.set_xticks(x)
            ax.set_xticklabels([m.upper() for m in model_names], fontsize=11)
            ax.set_title("Predictions by Model & Horizon",
                         fontsize=12, fontweight="bold")
            ax.set_ylabel("Predicted Price ($)")
            ax.legend(framealpha=0.3, labelcolor="#cccccc",
                      facecolor="#1a1a2e", edgecolor="#333355", fontsize=9)

        plt.suptitle(
            f"{self.ticker} Stock Price Prediction\n"
            f"LightGBM + Prophet + Chronos Ensemble  |  "
            f"As of {last_date.date()}",
            fontsize=14, fontweight="bold", color="#ffffff", y=1.01,
        )
        plt.tight_layout(pad=2.5)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            print(f"  Plot saved → {save_path}")
        else:
            plt.show()

        plt.close(fig)
