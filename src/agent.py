from langchain_openai import ChatOpenAI
from pathlib import Path
import json
import os
import re

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
FRONTEND_PAYLOAD_PATH = BASE_DIR / "outputs" / "frontend_payload.json"

my_api_key = os.getenv("OPENAI_API_KEY")

if not my_api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Export it before running main.py.")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=my_api_key
)


def risk_tool(asset: str) -> str:
    """Analyzes the financial risk of an asset."""
    return f"{asset} has moderate risk"


def available_assets() -> list[str]:
    assets = set()
    for csv_path in RAW_DATA_DIR.glob("*/*.csv"):
        assets.add(csv_path.stem.upper())
    payload = load_frontend_payload()
    for asset in payload.get("assets", []):
        ticker = asset.get("ticker")
        if ticker:
            assets.add(ticker.upper())
    return sorted(assets)


def load_frontend_payload() -> dict:
    if not FRONTEND_PAYLOAD_PATH.exists():
        return {}

    with FRONTEND_PAYLOAD_PATH.open() as payload_file:
        return json.load(payload_file)


def get_payload_asset(asset: str) -> dict | None:
    payload = load_frontend_payload()
    for item in payload.get("assets", []):
        if item.get("ticker", "").upper() == asset.upper():
            return item
    return None


def format_portfolio_analysis() -> str:
    payload = load_frontend_payload()
    if not payload:
        return f"No frontend payload found at {FRONTEND_PAYLOAD_PATH}."

    portfolio_summary = payload.get("portfolio_summary", {})
    assets = payload.get("assets", [])
    lines = [
        "Portfolio graphical analysis payload:",
        f"Payload source: {FRONTEND_PAYLOAD_PATH}",
        f"Generated at: {payload.get('generated_at', 'unknown')}",
        f"Asset count: {portfolio_summary.get('asset_count', len(assets))}",
        f"Top opportunities: {', '.join(portfolio_summary.get('top_opportunities', []))}",
        f"Highest risk assets: {', '.join(portfolio_summary.get('highest_risk_assets', []))}",
        f"Diversification candidates: {', '.join(portfolio_summary.get('diversification_candidates', []))}",
        f"Average opportunity score: {portfolio_summary.get('average_opportunity_score', 'n/a')}",
        f"Average risk score: {portfolio_summary.get('average_risk_score', 'n/a')}",
    ]

    ranked_assets = sorted(
        assets,
        key=lambda item: item.get("intelligence", {}).get("asset_rank", 999),
    )
    for item in ranked_assets[:5]:
        ticker = item.get("ticker", "n/a")
        intelligence = item.get("intelligence", {})
        recommendation = item.get("recommendation", {})
        lines.append(
            f"{ticker}: rank {intelligence.get('asset_rank', 'n/a')}, "
            f"opportunity {intelligence.get('opportunity_score', 'n/a')}, "
            f"risk {intelligence.get('risk_score', 'n/a')}, "
            f"action {recommendation.get('action', 'n/a')}"
        )

    return "\n".join(lines)


def format_frontend_analysis(asset: str) -> str:
    payload = load_frontend_payload()
    asset_payload = get_payload_asset(asset)

    if not payload:
        return f"No frontend payload found at {FRONTEND_PAYLOAD_PATH}."

    portfolio_summary = payload.get("portfolio_summary", {})
    generated_at = payload.get("generated_at", "unknown")

    lines = [
        "Frontend graphical analysis payload:",
        f"Payload source: {FRONTEND_PAYLOAD_PATH}",
        f"Generated at: {generated_at}",
    ]

    if portfolio_summary:
        lines.extend([
            f"Portfolio asset count: {portfolio_summary.get('asset_count', 'n/a')}",
            f"Top opportunities: {', '.join(portfolio_summary.get('top_opportunities', []))}",
            f"Highest risk assets: {', '.join(portfolio_summary.get('highest_risk_assets', []))}",
            f"Diversification candidates: {', '.join(portfolio_summary.get('diversification_candidates', []))}",
            f"Average opportunity score: {portfolio_summary.get('average_opportunity_score', 'n/a')}",
            f"Average risk score: {portfolio_summary.get('average_risk_score', 'n/a')}",
        ])

    if not asset_payload:
        return "\n".join(lines + [f"No asset-level frontend analysis found for {asset}."])

    intelligence = asset_payload.get("intelligence", {})
    recommendation = asset_payload.get("recommendation", {})
    projection = asset_payload.get("projection", {})
    total_return = intelligence.get("total_return", {})
    projected_range = projection.get("projected_range", {})

    lines.extend([
        f"Asset rank: {intelligence.get('asset_rank', 'n/a')}",
        f"Current price from payload: {intelligence.get('current_price', 'n/a')}",
        f"Payload date range: {intelligence.get('start_date', 'n/a')} to {intelligence.get('end_date', 'n/a')}",
        f"30d return: {total_return.get('30d', 'n/a')}%",
        f"1y return: {total_return.get('1y', 'n/a')}%",
        f"5y return: {total_return.get('5y', 'n/a')}%",
        f"Annualized return: {intelligence.get('annualized_return_pct', 'n/a')}%",
        f"Annualized volatility: {intelligence.get('annualized_volatility_pct', 'n/a')}%",
        f"Max drawdown: {intelligence.get('max_drawdown_pct', 'n/a')}%",
        f"Sharpe ratio: {intelligence.get('sharpe_ratio', 'n/a')}",
        f"Correlation with SPY: {intelligence.get('correlation_with_spy', 'n/a')}",
        f"24h return: {intelligence.get('recent_return_24h_pct', 'n/a')}%",
        f"5d return: {intelligence.get('recent_return_5d_pct', 'n/a')}%",
        f"Risk score: {intelligence.get('risk_score', 'n/a')}",
        f"Opportunity score: {intelligence.get('opportunity_score', 'n/a')}",
        f"Recommended action: {recommendation.get('action', 'n/a')}",
        f"Recommendation confidence: {recommendation.get('confidence', 'n/a')}",
        f"Risk level: {recommendation.get('risk_level', 'n/a')}",
        f"Recommendation rationale: {recommendation.get('rationale', 'n/a')}",
        f"Key drivers: {', '.join(recommendation.get('key_drivers', []))}",
        f"Projection horizon: {projection.get('projection_horizon_days', 'n/a')} days",
        f"Trend outlook: {projection.get('trend_outlook', 'n/a')}",
        f"Projection confidence: {projection.get('projection_confidence', 'n/a')}",
        (
            "Projected range: "
            f"low {projected_range.get('low', 'n/a')}, "
            f"mid {projected_range.get('mid', 'n/a')}, "
            f"high {projected_range.get('high', 'n/a')}"
        ),
        f"Scenario note: {projection.get('scenario_note', 'n/a')}",
    ])

    correlation_matrix = payload.get("correlation_matrix", {})
    asset_correlations = correlation_matrix.get(asset.upper(), {})
    if asset_correlations:
        strongest = sorted(
            ((ticker, value) for ticker, value in asset_correlations.items() if ticker != asset.upper()),
            key=lambda item: abs(item[1]),
            reverse=True,
        )[:3]
        lines.append(
            "Strongest correlations: "
            + ", ".join(f"{ticker}: {value}" for ticker, value in strongest)
        )

    return "\n".join(lines)


def parse_analysis_request(user_input: str) -> tuple[str, str]:
    text = user_input.strip()
    text_upper = text.upper()

    timeframe = "daily"
    if any(word in text_upper for word in ["HOURLY", "HOUR", "INTRADAY", "HORA", "HORARIO"]):
        timeframe = "hourly"
    elif any(word in text_upper for word in ["DAILY", "DAY", "DIA", "DIARIO"]):
        timeframe = "daily"

    for asset in available_assets():
        if re.search(rf"(?<![A-Z0-9.-]){re.escape(asset)}(?![A-Z0-9.-])", text_upper):
            return asset, timeframe

    if any(word in text_upper for word in ["PORTFOLIO", "CARTEIRA", "ALL ASSETS", "TODOS"]):
        return "PORTFOLIO", timeframe

    compact = re.sub(r"[^A-Z0-9.-]", "", text_upper)
    return compact, timeframe


def financial_analysis_tool(request: str) -> str:
    """Analyze one asset using CSV data and frontend_payload.json graphical intelligence."""
    try:
        import pandas as pd
    except ImportError as error:
        return (
            "Missing dependency for data analysis. Install it with:\n"
            "pip install pandas\n"
            f"Original error: {error}"
        )

    asset, timeframe = parse_analysis_request(request)
    if asset in {"PORTFOLIO", "CARTEIRA", "ALL", "TODOS"}:
        return (
            f"{format_portfolio_analysis()}\n"
            "Use this payload to explain the overall portfolio positioning, risk, opportunities, and diversification."
        )

    csv_path = RAW_DATA_DIR / timeframe / f"{asset}.csv"

    if not csv_path.exists():
        assets = ", ".join(available_assets())
        return (
            f"Could not find data for {asset} in {csv_path}.\n"
            f"Available assets: {assets}\n"
            "Ask with an asset and optionally the timeframe, for example: "
            "Analyze AAPL daily or Analyze BTC-USD hourly."
        )

    df = pd.read_csv(csv_path)

    date_col = "Date" if "Date" in df.columns else "Datetime"
    required_columns = {date_col, "Close"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        return (
            "The CSV file is missing required columns: "
            f"{', '.join(sorted(missing_columns))}.\n"
            "Expected at least: Date or Datetime, Close."
        )

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    asset_df = df.dropna(subset=[date_col, "Close"]).copy()

    if asset_df.empty:
        return f"No usable rows found in {csv_path}."

    asset_df = asset_df.sort_values(date_col)
    asset_df["Return"] = asset_df["Close"].pct_change()
    asset_df["MA_20"] = asset_df["Close"].rolling(window=20).mean()
    asset_df["MA_50"] = asset_df["Close"].rolling(window=50).mean()

    latest_price = asset_df["Close"].iloc[-1]
    first_price = asset_df["Close"].iloc[0]
    total_return = (latest_price / first_price - 1) * 100
    volatility = asset_df["Return"].std() * 100

    latest_ma20 = asset_df["MA_20"].iloc[-1]
    latest_ma50 = asset_df["MA_50"].iloc[-1]

    if pd.isna(latest_ma20) or pd.isna(latest_ma50):
        trend = "not enough data for 20/50-period moving average comparison"
    elif latest_ma20 > latest_ma50:
        trend = "positive trend: 20-period moving average is above the 50-period moving average"
    else:
        trend = "negative trend: 20-period moving average is below the 50-period moving average"

    running_max = asset_df["Close"].cummax()
    drawdown = (asset_df["Close"] / running_max - 1) * 100
    max_drawdown = drawdown.min()
    frontend_analysis = format_frontend_analysis(asset)

    return (
        "CSV data analysis:\n"
        f"Asset analyzed: {asset}\n"
        f"Timeframe: {timeframe}\n"
        f"CSV source: {csv_path}\n"
        f"Rows analyzed: {len(asset_df)}\n"
        f"Date range: {asset_df[date_col].iloc[0]} to {asset_df[date_col].iloc[-1]}\n"
        f"Latest close price: {latest_price:.2f}\n"
        f"Total return in dataset: {total_return:.2f}%\n"
        f"Daily volatility: {volatility:.2f}%\n"
        f"Maximum drawdown: {max_drawdown:.2f}%\n"
        f"20-period moving average: {latest_ma20:.2f}\n"
        f"50-period moving average: {latest_ma50:.2f}\n"
        f"Trend signal: {trend}\n"
        "\n"
        f"{frontend_analysis}\n"
        "Use both the CSV indicators and frontend graphical payload to explain risk, trend, recommendation, projection, and investment implications."
    )


try:
    from langchain.agents import initialize_agent
    from langchain.tools import Tool

    tools = [
        Tool(
            name="Risk Analyzer",
            func=risk_tool,
            description="Analyzes financial risk"
        ),
        Tool(
            name="Financial Analysis",
            func=financial_analysis_tool,
            description=(
                "Analyzes one asset using data/raw/daily or data/raw/hourly CSV files "
                "and outputs/frontend_payload.json. "
                "Input should include an asset ticker and optional timeframe, "
                "for example 'AAPL daily' or 'BTC-USD hourly'. "
                "calculates return, volatility, moving averages and drawdown, "
                "then enriches the answer with frontend graphical analysis, recommendations, "
                "portfolio rankings, correlations, and projections."
            )
        )
    ]

    agent = initialize_agent(
        tools,
        llm,
        agent="zero-shot-react-description",
        verbose=True
    )
except ImportError:
    from langchain.agents import create_agent
    from langchain.tools import tool

    @tool("risk_analyzer")
    def risk_analyzer(asset: str) -> str:
        """Analyzes the financial risk of an asset."""
        return risk_tool(asset)

    @tool("financial_analysis")
    def financial_analysis(request: str) -> str:
        """Analyzes one asset from CSV files and frontend_payload.json. Include ticker and optional timeframe."""
        return financial_analysis_tool(request)

    _agent = create_agent(
        model=llm,
        tools=[risk_analyzer, financial_analysis],
        system_prompt=(
            "You are a financial assistant. When the user asks about an asset, "
            "use financial_analysis to ground your answer in the CSV data and "
            "the frontend_payload.json graphical analysis. "
            "The available datasets are daily and hourly. "
            "Explain trend, volatility, drawdown, risk, recommendation, projection, "
            "correlations, and investment implications."
        ),
    )

    class AgentWrapper:
        def invoke(self, question: str):
            result = _agent.invoke(
                {"messages": [{"role": "user", "content": question}]})
            messages = result.get("messages", [])
            output = messages[-1].content if messages else str(result)
            return {"output": output}

    agent = AgentWrapper()
