import pandas as pd
import numpy as np
import os
import requests
from dotenv import load_dotenv

# Load environment variables from project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Ollama config
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def get_ollama_analysis(asset_name: str, current_price: float, sma_20: float, sma_50: float, signal: str) -> str:
    """Calls local Ollama API to generate a strategic analysis."""
    prompt = f"""You are an elite financial quantitative analyst for the 'Financial Bros' investment fund.
Write a brief, professional strategic analysis (max 3 sentences) for the asset {asset_name}.

Current Data:
- Current Price: ${current_price:.2f}
- 20-Day SMA (Short-term): ${sma_20:.2f}
- 50-Day SMA (Long-term): ${sma_50:.2f}
- Algorithmic Signal: {signal}

Provide an actionable insight on the technical momentum and what the fund manager should do.
Keep it concise, premium and strictly financial. No markdown."""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 150}
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            print(f"Ollama HTTP {response.status_code}: {response.text[:200]}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"Ollama not reachable at {OLLAMA_URL}")
        return None
    except requests.exceptions.Timeout:
        print(f"Ollama timeout for {asset_name}")
        return None
    except Exception as e:
        print(f"Ollama error for {asset_name}: {e}")
        return None


def generate_insights(df: pd.DataFrame, asset_name: str = "Unknown Asset", use_ai: bool = True):
    """
    Generates trading insights based on historical data.
    Uses SMA crossover strategy + local Ollama AI if available.
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
    df = df.copy()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    current_price = float(df['Close'].iloc[-1])
    sma_20 = float(df['SMA_20'].iloc[-1])
    sma_50 = float(df['SMA_50'].iloc[-1])
    prev_sma_20 = float(df['SMA_20'].iloc[-2])
    prev_sma_50 = float(df['SMA_50'].iloc[-2])

    signal = "HOLD"
    confidence = 0.5
    algorithmic_reason = "No clear trend identified."

    # SMA Crossover Strategy
    if sma_20 > sma_50 and prev_sma_20 <= prev_sma_50:
        signal = "BUY"
        confidence = 0.85
        algorithmic_reason = "Bullish Crossover: 20-day SMA crossed above 50-day SMA — strong momentum signal."
    elif sma_20 < sma_50 and prev_sma_20 >= prev_sma_50:
        signal = "SELL"
        confidence = 0.85
        algorithmic_reason = "Bearish Crossover: 20-day SMA crossed below 50-day SMA — exit signal triggered."
    elif sma_20 > sma_50:
        signal = "BUY"
        confidence = 0.6
        algorithmic_reason = "Uptrend: 20-day SMA is above 50-day SMA, sustained bullish momentum."
    elif sma_20 < sma_50:
        signal = "SELL"
        confidence = 0.6
        algorithmic_reason = "Downtrend: 20-day SMA is below 50-day SMA, bearish pressure persists."

    final_reason = algorithmic_reason
    if use_ai:
        ai_insight = get_ollama_analysis(asset_name, current_price, sma_20, sma_50, signal)
        if ai_insight:
            final_reason = f"🤖 AI Analysis: {ai_insight}"

    return {
        "signal": signal,
        "confidence": confidence,
        "reason": final_reason,
        "current_price": current_price,
        "sma_20": sma_20,
        "sma_50": sma_50
    }


def calculate_portfolio_metrics(asset_data_dict):
    """
    Calculates overall metrics for the portfolio (no AI calls to keep it fast).
    """
    signals = {"BUY": 0, "SELL": 0, "HOLD": 0}
    for asset, df in asset_data_dict.items():
        if df.empty:
            continue
        insights = generate_insights(df, asset, use_ai=False)
        signals[insights["signal"]] += 1
    return {
        "signals_distribution": signals,
        "total_assets": len(asset_data_dict)
    }


def chat_with_portfolio(message: str, portfolio_context: list) -> str:
    """Chat with Ollama about the portfolio."""
    context_str = "\n".join([
        f"- {a['asset']}: ${a['current_price']:.2f}, Signal: {a['signal']}"
        for a in portfolio_context
    ])
    prompt = f"""You are the Financial Bros AI advisor. Answer the following question about the investment portfolio.

Current Portfolio Status:
{context_str}

User Question: {message}

Provide a concise, professional financial answer. No markdown."""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.4, "num_predict": 300}
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        return "Ollama is not available. Please ensure it is running."
    except Exception as e:
        return f"AI Error: {str(e)}"
