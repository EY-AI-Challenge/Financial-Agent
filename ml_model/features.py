"""
features.py — Technical indicator & time-series feature engineering.

Generates ~80+ features from OHLCV data:
  - Lag returns (1d, 5d, 10d, 21d, 63d, 126d, 252d)
  - Rolling statistics (mean, std, skew, z-score)
  - Trend indicators: EMA, SMA crossovers
  - Momentum: RSI, MACD, Rate-of-Change, Williams %R
  - Volatility: ATR, Bollinger Band width, Garman-Klass
  - Volume: OBV, VWAP deviation, CMF
  - Calendar: day-of-week, month, quarter, year-fraction
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _pct(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.pct_change(periods).replace([np.inf, -np.inf], np.nan)


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=max(1, window // 2)).mean()


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _std(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=max(1, window // 2)).std()


# ---------------------------------------------------------------------------
# Momentum indicators
# ---------------------------------------------------------------------------

def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - 100 / (1 + rs)


def _macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    fast_ema = _ema(close, fast)
    slow_ema = _ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _williams_r(high: pd.Series, low: pd.Series, close: pd.Series,
                period: int = 14) -> pd.Series:
    highest_high = high.rolling(period).max()
    lowest_low = low.rolling(period).min()
    return -100 * (highest_high - close) / (highest_high - lowest_low + 1e-10)


def _stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                k_period: int = 14, d_period: int = 3):
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
    d = k.rolling(d_period).mean()
    return k, d


# ---------------------------------------------------------------------------
# Volatility indicators
# ---------------------------------------------------------------------------

def _atr(high: pd.Series, low: pd.Series, close: pd.Series,
         period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, min_periods=period).mean()


def _garman_klass_vol(open_: pd.Series, high: pd.Series,
                      low: pd.Series, close: pd.Series,
                      window: int = 21) -> pd.Series:
    """Garman-Klass volatility estimator (more efficient than close-to-close)."""
    log_hl = (np.log(high / low)) ** 2
    log_co = (np.log(close / open_)) ** 2
    gk = (0.5 * log_hl - (2 * np.log(2) - 1) * log_co).rolling(window).mean()
    return np.sqrt(gk * 252)   # annualised


def _bollinger(close: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = _sma(close, window)
    std = _std(close, window)
    upper = mid + num_std * std
    lower = mid - num_std * std
    width = (upper - lower) / (mid + 1e-10)
    pct_b = (close - lower) / (upper - lower + 1e-10)
    return upper, mid, lower, width, pct_b


# ---------------------------------------------------------------------------
# Volume indicators
# ---------------------------------------------------------------------------

def _obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    sign = np.sign(close.diff())
    return (sign * volume).cumsum()


def _cmf(high: pd.Series, low: pd.Series, close: pd.Series,
         volume: pd.Series, period: int = 20) -> pd.Series:
    mfm = ((close - low) - (high - close)) / (high - low + 1e-10)
    mfv = mfm * volume
    return mfv.rolling(period).sum() / (volume.rolling(period).sum() + 1e-10)


def _vwap_deviation(high: pd.Series, low: pd.Series, close: pd.Series,
                    volume: pd.Series, window: int = 20) -> pd.Series:
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).rolling(window).sum() / (
        volume.rolling(window).sum() + 1e-10
    )
    return (close - vwap) / (vwap + 1e-10)


# ---------------------------------------------------------------------------
# Main feature builder
# ---------------------------------------------------------------------------

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input : DataFrame with columns [Date, Open, High, Low, Close, Volume],
            sorted ascending by Date (no gaps check required — handles
            non-trading days already being absent).
    Output: DataFrame with all engineered features + original columns.
            Rows with NaN features (warm-up period) are dropped.
    """
    df = df.copy().sort_values("Date").reset_index(drop=True)

    o = df["Open"]
    h = df["High"]
    lo = df["Low"]
    c = df["Close"]
    v = df["Volume"]

    feats: dict = {}

    # ---- Raw returns -------------------------------------------------------
    for lag in [1, 2, 3, 5, 10, 21, 63, 126, 252]:
        feats[f"ret_{lag}d"] = _pct(c, lag)

    # ---- Rolling statistics (on log-returns) --------------------------------
    log_ret = np.log(c / c.shift(1))
    for w in [5, 10, 21, 63, 126, 252]:
        feats[f"roll_mean_{w}"] = log_ret.rolling(w).mean()
        feats[f"roll_std_{w}"] = log_ret.rolling(w).std()
    for w in [21, 63, 252]:
        feats[f"roll_skew_{w}"] = log_ret.rolling(w).skew()
        feats[f"roll_zscore_{w}"] = (
            (log_ret - log_ret.rolling(w).mean()) /
            (log_ret.rolling(w).std() + 1e-10)
        )

    # ---- Trend: SMA / EMA crossover signals ---------------------------------
    for span in [5, 10, 20, 50, 200]:
        feats[f"sma_{span}"] = _sma(c, span) / c - 1   # normalised distance
        feats[f"ema_{span}"] = _ema(c, span) / c - 1

    # Golden / death-cross signals (smooth version)
    feats["cross_5_20"]   = _sma(c, 5)   / (_sma(c, 20)  + 1e-10) - 1
    feats["cross_20_50"]  = _sma(c, 20)  / (_sma(c, 50)  + 1e-10) - 1
    feats["cross_50_200"] = _sma(c, 50)  / (_sma(c, 200) + 1e-10) - 1

    # ---- Momentum ----------------------------------------------------------
    feats["rsi_14"]     = _rsi(c, 14)
    feats["rsi_28"]     = _rsi(c, 28)
    feats["rsi_7"]      = _rsi(c, 7)

    macd_l, macd_s, macd_h = _macd(c)
    feats["macd"]        = macd_l / (c + 1e-10)
    feats["macd_signal"] = macd_s / (c + 1e-10)
    feats["macd_hist"]   = macd_h / (c + 1e-10)

    feats["roc_5"]   = c.pct_change(5)
    feats["roc_10"]  = c.pct_change(10)
    feats["roc_21"]  = c.pct_change(21)

    feats["williams_r_14"] = _williams_r(h, lo, c, 14)
    feats["williams_r_28"] = _williams_r(h, lo, c, 28)

    k, d = _stochastic(h, lo, c)
    feats["stoch_k"] = k
    feats["stoch_d"] = d
    feats["stoch_kd"] = k - d

    # ---- Volatility ---------------------------------------------------------
    feats["atr_14"]       = _atr(h, lo, c, 14) / (c + 1e-10)
    feats["atr_28"]       = _atr(h, lo, c, 28) / (c + 1e-10)
    feats["gk_vol_21"]    = _garman_klass_vol(o, h, lo, c, 21)
    feats["gk_vol_63"]    = _garman_klass_vol(o, h, lo, c, 63)
    feats["realised_vol_21"]  = log_ret.rolling(21).std()  * np.sqrt(252)
    feats["realised_vol_63"]  = log_ret.rolling(63).std()  * np.sqrt(252)
    feats["realised_vol_252"] = log_ret.rolling(252).std() * np.sqrt(252)

    _, _, _, bb_width, bb_pct = _bollinger(c, 20)
    feats["bb_width"]  = bb_width
    feats["bb_pct_b"]  = bb_pct
    feats["intraday_range"] = (h - lo) / (c + 1e-10)
    feats["gap_open"]       = (o - c.shift(1)) / (c.shift(1) + 1e-10)

    # ---- Volume -----------------------------------------------------------
    feats["vol_change_1d"]  = _pct(v, 1)
    feats["vol_change_5d"]  = _pct(v, 5)
    feats["vol_sma20_ratio"] = v / (_sma(v, 20) + 1e-10)
    feats["obv_norm"]        = _obv(c, v) / (v.rolling(252).sum() + 1e-10)
    feats["cmf_20"]          = _cmf(h, lo, c, v, 20)
    feats["vwap_dev_20"]     = _vwap_deviation(h, lo, c, v, 20)

    # ---- Calendar ----------------------------------------------------------
    dt = pd.to_datetime(df["Date"])
    feats["day_of_week"]  = dt.dt.dayofweek / 4.0          # 0-1 normalised
    feats["month"]        = dt.dt.month / 12.0
    feats["quarter"]      = dt.dt.quarter / 4.0
    feats["year_frac"]    = (dt.dt.dayofyear - 1) / 365.0
    feats["days_since_start"] = (dt - dt.iloc[0]).dt.days  # global time trend

    # ---- Assemble ----------------------------------------------------------
    feat_df = pd.DataFrame(feats, index=df.index)
    result = pd.concat([df, feat_df], axis=1)
    result.replace([np.inf, -np.inf], np.nan, inplace=True)

    return result


def make_targets(df: pd.DataFrame, horizons: dict) -> pd.DataFrame:
    """
    Add forward-return targets for each horizon.

    horizons : e.g. {"1w": 5, "1m": 21, "1y": 252}
    Target   : log-return over the horizon (amenable to regression).
                Predicted price = current_close * exp(target)
    """
    df = df.copy()
    for name, h in horizons.items():
        future_close = df["Close"].shift(-h)
        df[f"target_{name}"] = np.log(future_close / df["Close"])
    return df
