import pandas as pd
import numpy as np

def generate_insights(df: pd.DataFrame):
    """
    Generates trading insights based on historical data.
    Uses Simple Moving Averages (SMA) to determine trends and generate a basic signal.
    """
    if len(df) < 50:
        return {
            "signal": "HOLD",
            "confidence": 0.5,
            "reason": "Insufficient data for 50-day moving average.",
            "current_price": float(df['Close'].iloc[-1]) if not df.empty else 0.0,
            "sma_20": None,
            "sma_50": None
        }

    # Calculate SMAs
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    current_price = float(df['Close'].iloc[-1])
    sma_20 = float(df['SMA_20'].iloc[-1])
    sma_50 = float(df['SMA_50'].iloc[-1])
    
    prev_sma_20 = float(df['SMA_20'].iloc[-2])
    prev_sma_50 = float(df['SMA_50'].iloc[-2])

    signal = "HOLD"
    confidence = 0.5
    reason = "No clear trend identified."

    # Simple Crossover Strategy
    if sma_20 > sma_50 and prev_sma_20 <= prev_sma_50:
        signal = "BUY"
        confidence = 0.85
        reason = "Bullish Crossover: 20-day SMA crossed above 50-day SMA."
    elif sma_20 < sma_50 and prev_sma_20 >= prev_sma_50:
        signal = "SELL"
        confidence = 0.85
        reason = "Bearish Crossover: 20-day SMA crossed below 50-day SMA."
    elif sma_20 > sma_50:
        signal = "BUY"
        confidence = 0.6
        reason = "Uptrend: 20-day SMA is above 50-day SMA."
    elif sma_20 < sma_50:
        signal = "SELL"
        confidence = 0.6
        reason = "Downtrend: 20-day SMA is below 50-day SMA."

    return {
        "signal": signal,
        "confidence": confidence,
        "reason": reason,
        "current_price": current_price,
        "sma_20": sma_20,
        "sma_50": sma_50
    }

def calculate_portfolio_metrics(asset_data_dict):
    """
    Calculates overall metrics for the portfolio.
    """
    total_value = 0
    signals = {"BUY": 0, "SELL": 0, "HOLD": 0}
    
    for asset, df in asset_data_dict.items():
        if df.empty:
            continue
        insights = generate_insights(df)
        signals[insights["signal"]] += 1
        
    return {
        "signals_distribution": signals,
        "total_assets": len(asset_data_dict)
    }
