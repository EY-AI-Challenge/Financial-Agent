import os
from typing import Optional, Dict, Any
from backend.data_router import get_ticker_history

import pandas as pd
import numpy as np


TRADING_DAYS = 252


def load_data(ticker: Optional[str] = None, filepath: Optional[str] = None) -> pd.DataFrame:
    """Load OHLCV price data for a ticker.
 
    Resolution order:
    1. Explicit filepath - read the CSV directly.
    2. data_router       - calls get_ticker_history(ticker), which returns a
                           list of dicts (df.to_dict('records') shape).
                           Date values arrive as strings; pd.to_datetime
                           handles them correctly.
 
    The returned DataFrame is sorted and indexed by Date.
    """
    if filepath:
        df = pd.read_csv(filepath)
    elif ticker:
        records = get_ticker_history(ticker)
        df = pd.DataFrame(records)
    else:
        raise ValueError("Either ticker or filepath must be provided")
 
    if "Date" not in df.columns:
        raise ValueError("Data must contain a 'Date' column")
    if "Close" not in df.columns:
        raise ValueError("Data must contain a 'Close' column")
 
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")
 
    return df



# ---------------------------------------------------------------------------
# Core return / risk helpers
# ---------------------------------------------------------------------------
 
def calculate_daily_returns(prices: pd.Series) -> pd.Series:
    """Daily simple returns."""
    return prices.pct_change().dropna()
 
 
def calculate_log_returns(prices: pd.Series) -> pd.Series:
    """Daily log returns (continuously compounded)."""
    return np.log(prices / prices.shift(1)).dropna()
 
 
def annualized_return(returns: pd.Series) -> float:
    """Annualized arithmetic mean return."""
    return (1 + returns.mean()) ** TRADING_DAYS - 1
 
 
def annualized_volatility(returns: pd.Series) -> float:
    """Annualized standard deviation of returns."""
    return returns.std() * np.sqrt(TRADING_DAYS)
 
 
def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe ratio."""
    vol = annualized_volatility(returns)
    return (annualized_return(returns) - risk_free_rate) / vol if vol != 0 else np.nan
 
 
def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0,
                  target: float = 0.0) -> float:
    """Annualized Sortino ratio (penalises only downside deviation)."""
    downside = returns[returns < target]
    downside_vol = downside.std() * np.sqrt(TRADING_DAYS) if len(downside) > 1 else np.nan
    if not downside_vol or downside_vol == 0:
        return np.nan
    return (annualized_return(returns) - risk_free_rate) / downside_vol
 
 
def calmar_ratio(prices: pd.Series) -> float:
    """CAGR divided by absolute max drawdown."""
    mdd = abs(max_drawdown(prices))
    if mdd == 0:
        return np.nan
    return cagr(prices) / mdd
 
 
def cagr(prices: pd.Series) -> float:
    """Compound Annual Growth Rate."""
    n_years = (prices.index[-1] - prices.index[0]).days / 365.25
    if n_years <= 0:
        return np.nan
    return (prices.iloc[-1] / prices.iloc[0]) ** (1 / n_years) - 1
 
 
def max_drawdown(prices: pd.Series) -> float:
    """Maximum peak-to-trough drawdown (negative value)."""
    rolling_max = prices.cummax()
    return ((prices / rolling_max) - 1).min()
 
 
def value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    """Historical VaR at the given confidence level (daily, negative value)."""
    return np.percentile(returns, (1 - confidence) * 100)
 
 
def conditional_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Expected Shortfall / CVaR (average of worst losses beyond VaR)."""
    var = value_at_risk(returns, confidence)
    tail = returns[returns <= var]
    return tail.mean() if len(tail) > 0 else np.nan
 
 
def beta(returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Beta relative to a benchmark."""
    aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
    if len(aligned) < 2:
        return np.nan
    cov_matrix = aligned.cov()
    return cov_matrix.iloc[0, 1] / cov_matrix.iloc[1, 1]
 
 
def alpha(returns: pd.Series, benchmark_returns: pd.Series,
          risk_free_rate: float = 0.0) -> float:
    """Jensen's alpha (annualized)."""
    b = beta(returns, benchmark_returns)
    if np.isnan(b):
        return np.nan
    return (annualized_return(returns) - risk_free_rate
            - b * (annualized_return(benchmark_returns) - risk_free_rate))
 
 
# ---------------------------------------------------------------------------
# Price / moving-average helpers
# ---------------------------------------------------------------------------
 
def moving_average(prices: pd.Series, window: int) -> float:
    """Last value of a simple moving average."""
    return prices.rolling(window=window).mean().iloc[-1] if len(prices) >= window else np.nan
 
 
def exponential_moving_average(prices: pd.Series, span: int) -> float:
    """Last value of an exponential moving average."""
    return prices.ewm(span=span, adjust=False).mean().iloc[-1] if len(prices) >= span else np.nan
 
 
def relative_strength_index(prices: pd.Series, window: int = 14) -> float:
    """RSI (Wilder smoothing)."""
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))
    return rsi_series.iloc[-1] if not rsi_series.empty else np.nan
 
 
def bollinger_bands(prices: pd.Series, window: int = 20,
                    num_std: float = 2.0) -> Dict[str, float]:
    """Upper, middle (SMA) and lower Bollinger Bands (last values)."""
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    return {
        "upper": (sma + num_std * std).iloc[-1],
        "middle": sma.iloc[-1],
        "lower": (sma - num_std * std).iloc[-1],
    }
 
 
def recent_return(prices: pd.Series, periods: int = 21) -> float:
    """Return over the last `periods` trading days."""
    return prices.pct_change(periods=periods).iloc[-1] if len(prices) > periods else np.nan
 
 
# ---------------------------------------------------------------------------
# Volume helpers (require OHLCV DataFrame)
# ---------------------------------------------------------------------------
 
def average_volume(df: pd.DataFrame, window: int = 20) -> float:
    """Average Volume over the last `window` days."""
    if "Volume" not in df.columns or len(df) < window:
        return np.nan
    return df["Volume"].rolling(window=window).mean().iloc[-1]
 
 
def on_balance_volume(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume series."""
    if "Volume" not in df.columns:
        return pd.Series(dtype=float)
    direction = np.sign(df["Close"].diff()).fillna(0)
    return (direction * df["Volume"]).cumsum()
 
 
# ---------------------------------------------------------------------------
# Drawdown series (for charting)
# ---------------------------------------------------------------------------
 
def drawdown_series(prices: pd.Series) -> pd.Series:
    """Full drawdown time series (values <= 0)."""
    return (prices / prices.cummax()) - 1
 
 
# ---------------------------------------------------------------------------
# Cumulative return series (for charting)
# ---------------------------------------------------------------------------
 
def cumulative_return_series(returns: pd.Series) -> pd.Series:
    """Cumulative simple return series starting at 0."""
    return (1 + returns).cumprod() - 1
 
 
# ---------------------------------------------------------------------------
# Rolling metrics (for charting)
# ---------------------------------------------------------------------------
 
def rolling_volatility_series(returns: pd.Series,
                               window: int = 21) -> pd.Series:
    """Annualized rolling volatility series."""
    return returns.rolling(window=window).std() * np.sqrt(TRADING_DAYS)
 
 
def rolling_sharpe_series(returns: pd.Series, window: int = 63,
                           risk_free_rate: float = 0.0) -> pd.Series:
    """Rolling Sharpe ratio series."""
    roll_ret = returns.rolling(window=window).apply(annualized_return, raw=False)
    roll_vol = returns.rolling(window=window).apply(annualized_volatility, raw=False)
    return (roll_ret - risk_free_rate) / roll_vol   
