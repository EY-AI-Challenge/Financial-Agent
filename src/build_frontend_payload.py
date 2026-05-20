from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DAILY_DIR = BASE_DIR / "data" / "raw" / "daily"
HOURLY_DIR = BASE_DIR / "data" / "raw" / "hourly"
OUTPUT_PATH = BASE_DIR / "outputs" / "frontend_payload.json"

TRADING_DAYS = 252


@dataclass
class AssetFrames:
    daily: pd.DataFrame
    hourly: pd.DataFrame | None


def load_asset_frames() -> dict[str, AssetFrames]:
    assets: dict[str, AssetFrames] = {}

    for csv_path in sorted(DAILY_DIR.glob("*.csv")):
        daily = pd.read_csv(csv_path)
        daily["Date"] = pd.to_datetime(daily["Date"])
        daily = daily.sort_values("Date").reset_index(drop=True)
        assets[csv_path.stem] = AssetFrames(daily=daily, hourly=None)

    for csv_path in sorted(HOURLY_DIR.glob("*.csv")):
        if csv_path.stem not in assets:
            continue
        hourly = pd.read_csv(csv_path)
        hourly["Datetime"] = pd.to_datetime(hourly["Datetime"], utc=True)
        hourly = hourly.sort_values("Datetime").reset_index(drop=True)
        assets[csv_path.stem].hourly = hourly

    return assets


def annualized_return(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    compounded = (1 + clean).prod()
    return compounded ** (TRADING_DAYS / len(clean)) - 1


def annualized_volatility(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    return clean.std() * np.sqrt(TRADING_DAYS)


def sharpe_ratio(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    vol = annualized_volatility(clean)
    if vol == 0 or np.isnan(vol):
        return float("nan")
    return annualized_return(clean) / vol


def max_drawdown(prices: pd.Series) -> float:
    running_max = prices.cummax()
    drawdown = prices / running_max - 1
    return float(drawdown.min())


def total_return(prices: pd.Series, periods: int) -> float | None:
    if len(prices) <= periods:
        return None
    return float(prices.iloc[-1] / prices.iloc[-periods - 1] - 1)


def normalize_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    valid = series.replace([np.inf, -np.inf], np.nan)
    if valid.dropna().empty:
        return pd.Series(50.0, index=series.index)
    min_val = valid.min()
    max_val = valid.max()
    if pd.isna(min_val) or pd.isna(max_val) or min_val == max_val:
        return pd.Series(50.0, index=series.index)
    scaled = (valid - min_val) / (max_val - min_val) * 100
    if not higher_is_better:
        scaled = 100 - scaled
    return scaled.fillna(50.0)


def classify_risk(risk_score: float) -> str:
    if risk_score >= 67:
        return "high"
    if risk_score >= 34:
        return "medium"
    return "low"


def classify_confidence(opportunity_score: float, risk_score: float) -> str:
    spread = opportunity_score - risk_score
    if spread >= 20:
        return "high"
    if spread >= 5:
        return "medium"
    return "low"


def recommendation_label(opportunity_score: float, risk_score: float) -> str:
    if opportunity_score >= 65 and risk_score <= 55:
        return "buy"
    if risk_score >= 70 and opportunity_score <= 50:
        return "reduce"
    return "hold"


def projection_from_signals(
    current_price: float,
    momentum_30d: float | None,
    momentum_90d: float | None,
    volatility: float,
) -> dict[str, object]:
    momentum_30d = 0.0 if momentum_30d is None else momentum_30d
    momentum_90d = 0.0 if momentum_90d is None else momentum_90d

    weighted_signal = 0.65 * momentum_30d + 0.35 * momentum_90d
    horizon_days = 90
    projected_mid = current_price * (1 + weighted_signal * 0.6)
    band = current_price * max(volatility, 0.08) * 0.35

    if weighted_signal > 0.08:
        outlook = "bullish"
    elif weighted_signal < -0.08:
        outlook = "bearish"
    else:
        outlook = "neutral"

    confidence = "high" if volatility < 0.25 else "medium" if volatility < 0.45 else "low"

    return {
        "projection_horizon_days": horizon_days,
        "trend_outlook": outlook,
        "projection_confidence": confidence,
        "projected_range": {
            "low": round(projected_mid - band, 2),
            "mid": round(projected_mid, 2),
            "high": round(projected_mid + band, 2),
        },
        "scenario_note": (
            f"{outlook.capitalize()} short-term scenario driven by recent momentum "
            f"with volatility-adjusted uncertainty bands."
        ),
    }


def main() -> None:
    assets = load_asset_frames()

    price_frames = []
    metric_rows: list[dict[str, object]] = []

    for ticker, frames in assets.items():
        daily = frames.daily.copy()
        daily["daily_return"] = daily["Adj Close"].pct_change()
        returns = daily["daily_return"]
        prices = daily["Adj Close"]

        row = {
            "ticker": ticker,
            "start_date": daily["Date"].min(),
            "end_date": daily["Date"].max(),
            "current_price": float(prices.iloc[-1]),
            "total_return_30d": total_return(prices, 30),
            "total_return_1y": total_return(prices, 252),
            "total_return_5y": float(prices.iloc[-1] / prices.iloc[0] - 1),
            "annualized_return": float(annualized_return(returns)),
            "annualized_volatility": float(annualized_volatility(returns)),
            "sharpe_ratio": float(sharpe_ratio(returns)),
            "max_drawdown": max_drawdown(prices),
            "momentum_30d": total_return(prices, 30),
            "momentum_90d": total_return(prices, 90),
            "average_volume": float(daily["Volume"].mean()),
        }

        if frames.hourly is not None and len(frames.hourly) > 24:
            hourly_prices = frames.hourly["Adj Close"]
            row["recent_return_24h"] = float(hourly_prices.iloc[-1] / hourly_prices.iloc[-24] - 1)
            lookback = min(35, len(hourly_prices) - 1)
            row["recent_return_5d"] = float(hourly_prices.iloc[-1] / hourly_prices.iloc[-lookback] - 1)
        else:
            row["recent_return_24h"] = None
            row["recent_return_5d"] = None

        metric_rows.append(row)
        price_frames.append(daily[["Date", "Adj Close"]].rename(columns={"Adj Close": ticker}).set_index("Date"))

    metrics_df = pd.DataFrame(metric_rows).sort_values("ticker").reset_index(drop=True)
    price_df = pd.concat(price_frames, axis=1).sort_index()
    returns_df = price_df.pct_change(fill_method=None)
    corr_df = returns_df.corr()

    metrics_df["correlation_with_spy"] = metrics_df["ticker"].map(corr_df["SPY"]).fillna(0.0)

    opportunity_components = pd.DataFrame(
        {
            "ret_5y": normalize_score(metrics_df["total_return_5y"]),
            "ret_1y": normalize_score(metrics_df["total_return_1y"]),
            "mom_30d": normalize_score(metrics_df["momentum_30d"]),
            "sharpe": normalize_score(metrics_df["sharpe_ratio"]),
        }
    )
    metrics_df["opportunity_score"] = opportunity_components.mean(axis=1)

    risk_components = pd.DataFrame(
        {
            "volatility": normalize_score(metrics_df["annualized_volatility"], higher_is_better=False),
            "drawdown": normalize_score(metrics_df["max_drawdown"].abs(), higher_is_better=False),
            "spy_corr": normalize_score(metrics_df["correlation_with_spy"].abs(), higher_is_better=False),
        }
    )
    metrics_df["risk_score"] = 100 - risk_components.mean(axis=1)

    metrics_df["asset_rank"] = metrics_df["opportunity_score"].rank(ascending=False, method="dense").astype(int)

    assets_payload = []
    for _, row in metrics_df.sort_values("asset_rank").iterrows():
        recommendation = recommendation_label(row["opportunity_score"], row["risk_score"])
        confidence = classify_confidence(row["opportunity_score"], row["risk_score"])
        risk_level = classify_risk(row["risk_score"])

        drivers = []
        if (row["momentum_30d"] or 0) > 0:
            drivers.append("positive recent momentum")
        if row["sharpe_ratio"] > 0.5:
            drivers.append("strong risk-adjusted profile")
        if row["annualized_volatility"] > 0.45:
            drivers.append("elevated volatility")
        if abs(row["max_drawdown"]) > 0.5:
            drivers.append("deep historical drawdown")
        if abs(row["correlation_with_spy"]) < 0.3:
            drivers.append("diversification benefit")
        drivers = drivers[:3] or ["balanced signal profile"]

        rationale = (
            f"{row['ticker']} shows {risk_level} risk with an opportunity score of "
            f"{row['opportunity_score']:.1f}. Recommendation is {recommendation} "
            f"based on {', '.join(drivers)}."
        )

        projection = projection_from_signals(
            current_price=row["current_price"],
            momentum_30d=row["momentum_30d"],
            momentum_90d=row["momentum_90d"],
            volatility=row["annualized_volatility"],
        )

        assets_payload.append(
            {
                "ticker": row["ticker"],
                "intelligence": {
                    "current_price": round(row["current_price"], 2),
                    "start_date": row["start_date"].date().isoformat(),
                    "end_date": row["end_date"].date().isoformat(),
                    "total_return": {
                        "30d": round(row["total_return_30d"] * 100, 2) if pd.notna(row["total_return_30d"]) else None,
                        "1y": round(row["total_return_1y"] * 100, 2) if pd.notna(row["total_return_1y"]) else None,
                        "5y": round(row["total_return_5y"] * 100, 2),
                    },
                    "annualized_return_pct": round(row["annualized_return"] * 100, 2),
                    "annualized_volatility_pct": round(row["annualized_volatility"] * 100, 2),
                    "max_drawdown_pct": round(row["max_drawdown"] * 100, 2),
                    "sharpe_ratio": round(row["sharpe_ratio"], 2) if pd.notna(row["sharpe_ratio"]) else None,
                    "correlation_with_spy": round(row["correlation_with_spy"], 2),
                    "recent_return_24h_pct": round(row["recent_return_24h"] * 100, 2) if pd.notna(row["recent_return_24h"]) else None,
                    "recent_return_5d_pct": round(row["recent_return_5d"] * 100, 2) if pd.notna(row["recent_return_5d"]) else None,
                    "risk_score": round(row["risk_score"], 1),
                    "opportunity_score": round(row["opportunity_score"], 1),
                    "asset_rank": int(row["asset_rank"]),
                },
                "recommendation": {
                    "action": recommendation,
                    "confidence": confidence,
                    "risk_level": risk_level,
                    "rationale": rationale,
                    "key_drivers": drivers,
                },
                "projection": projection,
            }
        )

    top_assets = metrics_df.sort_values("opportunity_score", ascending=False)["ticker"].head(3).tolist()
    risk_assets = metrics_df.sort_values("risk_score", ascending=False)["ticker"].head(3).tolist()
    diversifiers = metrics_df.sort_values("correlation_with_spy", ascending=True)["ticker"].head(3).tolist()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "portfolio_summary": {
            "asset_count": int(len(metrics_df)),
            "top_opportunities": top_assets,
            "highest_risk_assets": risk_assets,
            "diversification_candidates": diversifiers,
            "average_opportunity_score": round(float(metrics_df["opportunity_score"].mean()), 1),
            "average_risk_score": round(float(metrics_df["risk_score"].mean()), 1),
        },
        "assets": assets_payload,
        "correlation_matrix": corr_df.round(3).fillna(0.0).to_dict(),
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Saved frontend payload to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
