"""
Financial tools for the LangGraph agent.
All market data comes from CSV files produced by DataLoader.py (offline demo).
"""

import ast
import operator
import os
from typing import Optional

import pandas as pd
from langchain_core.tools import tool

from Config import (
    DATA_FOLDER,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    STOCKS,
)
from decision_engine import format_prediction, predict_signal, train_model

# Cache CSV data in memory so each tool call does not re-read every file
_market_cache: Optional[dict] = None


def _get_market_data() -> dict:
    """Load all stock CSVs once and reuse them for every tool call (no console spam)."""
    global _market_cache
    if _market_cache is None:
        data = {}
        for ticker in STOCKS:
            path = os.path.join(DATA_FOLDER, f"{ticker}.csv")
            if os.path.exists(path):
                data[ticker] = pd.read_csv(path, index_col=0, parse_dates=True)
        _market_cache = data
    return _market_cache


def _normalize_ticker(ticker: str) -> str:
    """Uppercase ticker and strip spaces (e.g. ' aapl ' -> 'AAPL')."""
    return ticker.strip().upper()


def _latest_row(ticker: str):
    """
    Return the most recent row for a ticker.
    Raises ValueError if ticker is unknown or CSV is missing.
    """
    ticker = _normalize_ticker(ticker)
    data = _get_market_data()

    if ticker not in data:
        available = ", ".join(sorted(data.keys())) if data else "none — run DataLoader.py first"
        raise ValueError(f"Unknown or missing ticker '{ticker}'. Available: {available}")

    df = data[ticker]
    if df.empty:
        raise ValueError(f"No rows in CSV for {ticker}")

    return df.iloc[-1], df.index[-1]


def _trend_label(close: float, ma_20: float, ma_50: float) -> str:
    """Simple trend label from price vs moving averages."""
    if close > ma_20 > ma_50:
        return "uptrend"
    if close < ma_20 < ma_50:
        return "downtrend"
    return "mixed"


# ── LangChain tools (callable by the agent) ───────────────────────────────────

@tool
def list_available_stocks() -> str:
    """
    List stock tickers that have CSV data loaded.
    Call this when the user asks which assets you can analyse.
    """
    data = _get_market_data()
    if not data:
        return "No market data loaded. Run: python DataLoader.py"
    lines = [f"- {t}" for t in sorted(data.keys())]
    return "Available stocks:\n" + "\n".join(lines)


@tool
def get_stock_summary(ticker: str) -> str:
    """
    Latest price and technical indicators for one stock (from CSV).
    Use for questions about current price, RSI, MACD, or trend.
    ticker: e.g. AAPL, MSFT, GOOGL
    """
    row, as_of = _latest_row(ticker)
    t = _normalize_ticker(ticker)

    close = float(row["close"])
    rsi = float(row["rsi_14"])
    macd = float(row["macd"])
    macd_signal = float(row["macd_signal"])
    ma_20 = float(row["ma_20"])
    ma_50 = float(row["ma_50"])
    vol = float(row["volatility_20"])
    ret_1d = float(row["return_1d"]) * 100
    ret_5d = float(row["return_5d"]) * 100
    trend = _trend_label(close, ma_20, ma_50)

    macd_bias = "bullish" if macd > macd_signal else "bearish"

    return (
        f"Stock: {t} (as of {as_of.date()})\n"
        f"Close: USD {close:.2f}\n"
        f"1-day return: {ret_1d:+.2f}% | 5-day return: {ret_5d:+.2f}%\n"
        f"RSI(14): {rsi:.1f} | MACD: {macd:.3f} (signal {macd_signal:.3f}, {macd_bias})\n"
        f"MA20: USD {ma_20:.2f} | MA50: USD {ma_50:.2f} | Trend: {trend}\n"
        f"Volatility (20d): {vol:.4f}"
    )


def _rule_based_signal(ticker: str) -> str:
    """Fallback RSI signal when ML model is unavailable."""
    row, as_of = _latest_row(ticker)
    t = _normalize_ticker(ticker)
    rsi = float(row["rsi_14"])
    close = float(row["close"])
    ma_20 = float(row["ma_20"])

    if rsi < RSI_OVERSOLD:
        signal = "BUY"
        reason = f"RSI {rsi:.1f} below oversold ({RSI_OVERSOLD})"
    elif rsi > RSI_OVERBOUGHT:
        signal = "SELL"
        reason = f"RSI {rsi:.1f} above overbought ({RSI_OVERBOUGHT})"
    else:
        signal = "HOLD"
        reason = f"RSI {rsi:.1f} between {RSI_OVERSOLD} and {RSI_OVERBOUGHT}"

    price_vs_ma = "above MA20" if close > ma_20 else "below MA20"
    return (
        f"Rule-based signal for {t} (as of {as_of.date()}): {signal}\n"
        f"Reason: {reason}\n"
        f"Close: USD {close:.2f} | {price_vs_ma} | MA20: USD {ma_20:.2f}"
    )


@tool
def get_trading_signal(ticker: str) -> str:
    """
    Trading signal from ML model (RandomForest classifier from model.ipynb).
    Falls back to RSI rules if the model cannot load.
    Returns BUY, SELL, or HOLD with confidence.
    ticker: e.g. AAPL, MSFT
    """
    t = _normalize_ticker(ticker)
    try:
        result = predict_signal(t)
        return format_prediction(result)
    except Exception as e:
        return (
            f"ML signal unavailable ({e}). Using rule-based fallback:\n\n"
            + _rule_based_signal(t)
            + "\nDisclaimer: decision support only, not guaranteed returns."
        )


@tool
def train_ml_model() -> str:
    """
    Retrain the RandomForest model from data/*.csv and save to models/.
    Call when the user asks to refresh or train the ML model.
    """
    try:
        metrics = train_model()
        return (
            "ML model trained and saved.\n"
            f"Train accuracy: {metrics['train_accuracy']:.1%}\n"
            f"Validation accuracy: {metrics['val_accuracy']:.1%}\n"
            f"Test accuracy: {metrics['test_accuracy']:.1%}\n"
            f"Rows used: {metrics['rows']}"
        )
    except Exception as e:
        return f"Training failed: {e}"


@tool
def compare_stocks(tickers: str) -> str:
    """
    Compare latest metrics for multiple stocks side by side.
    tickers: comma-separated list, e.g. 'AAPL,MSFT,GOOGL'
    """
    parts = [p.strip() for p in tickers.split(",") if p.strip()]
    if len(parts) < 2:
        return "Provide at least two tickers separated by commas, e.g. AAPL,MSFT"

    lines = []
    for raw in parts:
        row, as_of = _latest_row(raw)
        t = _normalize_ticker(raw)
        close = float(row["close"])
        rsi = float(row["rsi_14"])
        ret_5d = float(row["return_5d"]) * 100
        lines.append(
            f"{t}: close=USD {close:.2f}, RSI={rsi:.1f}, 5d return={ret_5d:+.2f}% (as of {as_of.date()})"
        )

    return "Comparison:\n" + "\n".join(lines)


@tool
def calculator(expression: str) -> str:
    """
    Safe calculator for ROI, percentages, and simple math.
    Only numbers and operators + - * / ( ) are allowed.
    """
    try:
        result = _safe_eval(expression)
        return str(result)
    except Exception as e:
        return f"Calculator error: {e}"


# ── Safe math (no eval on arbitrary code) ─────────────────────────────────────

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(expression: str) -> float:
    """Evaluate a numeric expression using AST only (no eval())."""
    expression = expression.strip()
    if not expression:
        raise ValueError("Empty expression")

    tree = ast.parse(expression, mode="eval")

    def _eval_node(node):
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub):
            return _ALLOWED_OPS[type(node.op)](_eval_node(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            return _ALLOWED_OPS[type(node.op)](left, right)
        raise ValueError("Only basic arithmetic is allowed (+ - * / numbers parentheses)")

    return _eval_node(tree)


# All tools wired into the agent (import this list in agent.py)
FINANCIAL_TOOLS = [
    list_available_stocks,
    get_stock_summary,
    get_trading_signal,
    train_ml_model,
    compare_stocks,
    calculator,
]
