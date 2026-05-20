import pandas as pd
import numpy as np
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use the recommended model for text generation
    model = genai.GenerativeModel('gemini-1.5-pro')

def get_gemini_analysis(asset_name: str, current_price: float, sma_20: float, sma_50: float, signal: str) -> str:
    """Calls Gemini API to generate a strategic analysis."""
    if not GEMINI_API_KEY:
        return None
        
    prompt = f"""
    You are an elite financial quantitative analyst for the 'Financial Bros' investment fund.
    You need to write a brief, professional, and highly strategic analysis (max 3 sentences) for the asset {asset_name}.
    
    Current Data:
    - Current Price: ${current_price:.2f}
    - 20-Day SMA (Short-term): ${sma_20:.2f}
    - 50-Day SMA (Long-term): ${sma_50:.2f}
    - Algorithmic Signal Generated: {signal}
    
    Provide an actionable insight explaining the technical momentum and what the fund manager should consider doing.
    Keep it concise, premium, and strictly financial. Do not use markdown styling.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Gemini API failed to generate insight. Please check your quota or connection."

def generate_insights(df: pd.DataFrame, asset_name: str = "Unknown Asset"):
    """
    Generates trading insights based on historical data.
    Uses Simple Moving Averages (SMA) and conditionally uses Gemini AI if configured.
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
    algorithmic_reason = "No clear trend identified."

    # Simple Crossover Strategy
    if sma_20 > sma_50 and prev_sma_20 <= prev_sma_50:
        signal = "BUY"
        confidence = 0.85
        algorithmic_reason = "Bullish Crossover: 20-day SMA crossed above 50-day SMA."
    elif sma_20 < sma_50 and prev_sma_20 >= prev_sma_50:
        signal = "SELL"
        confidence = 0.85
        algorithmic_reason = "Bearish Crossover: 20-day SMA crossed below 50-day SMA."
    elif sma_20 > sma_50:
        signal = "BUY"
        confidence = 0.6
        algorithmic_reason = "Uptrend: 20-day SMA is above 50-day SMA."
    elif sma_20 < sma_50:
        signal = "SELL"
        confidence = 0.6
        algorithmic_reason = "Downtrend: 20-day SMA is below 50-day SMA."

    # Decide on the final reason string
    final_reason = algorithmic_reason
    if GEMINI_API_KEY:
        gemini_insight = get_gemini_analysis(asset_name, current_price, sma_20, sma_50, signal)
        if gemini_insight:
            final_reason = f"🤖 Gemini Analysis: {gemini_insight}"

    return {
        "signal": signal,
        "confidence": confidence,
        "reason": final_reason,
        "current_price": current_price,
        "sma_20": sma_20,
        "sma_50": sma_50
    }

def chat_with_portfolio(user_message: str, portfolio_context: list) -> str:
    """Answers a free-form question using live portfolio data as context."""
    if not GEMINI_API_KEY:
        return "Gemini API key not configured. Add GEMINI_API_KEY to your .env file."

    lines = []
    for a in portfolio_context:
        sma20 = f"${a['sma_20']:.2f}" if a.get('sma_20') else "N/A"
        sma50 = f"${a['sma_50']:.2f}" if a.get('sma_50') else "N/A"
        lines.append(
            f"- {a['asset']}: Price ${a['current_price']:.2f} | Signal {a['signal']} ({a['confidence']*100:.0f}%) | SMA20 {sma20} | SMA50 {sma50}"
        )
    context_str = "\n".join(lines)

    prompt = f"""You are an elite AI financial advisor for the 'Financial Bros' investment fund.
You have real-time access to the fund's full portfolio data shown below.
Answer the user's question concisely, professionally, and in the same language the user used.

CURRENT PORTFOLIO DATA:
{context_str}

USER QUESTION: {user_message}

Reply in 2-4 sentences. Be specific with asset names and numbers. Do not use markdown."""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"


def calculate_portfolio_metrics(asset_data_dict):
    """
    Calculates overall metrics for the portfolio.
    """
    total_value = 0
    signals = {"BUY": 0, "SELL": 0, "HOLD": 0}
    
    for asset, df in asset_data_dict.items():
        if df.empty:
            continue
        # We only pass asset name for individual insights to save API calls
        # Here we just use default 'Unknown Asset' because we just want the signal count, 
        # but to save API costs, we could disable Gemini here. For simplicity, it will call it 
        # unless we pass a flag. Let's just pass the asset name.
        insights = generate_insights(df, asset)
        signals[insights["signal"]] += 1
        
    return {
        "signals_distribution": signals,
        "total_assets": len(asset_data_dict)
    }
