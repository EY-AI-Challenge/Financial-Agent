from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from agent import available_assets, format_portfolio_analysis, get_payload_asset  # noqa: E402
from agent import agent as financial_agent  # noqa: E402

PAYLOAD_PATH = BASE_DIR / "outputs" / "frontend_payload.json"

st.set_page_config(
    page_title="EY AI Portfolio Copilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
    .stMetric {
        background-color: #111827;
        padding: 14px;
        border-radius: 10px;
        border: 1px solid #374151;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def load_payload() -> dict:
    if not PAYLOAD_PATH.exists():
        return {}
    return json.loads(PAYLOAD_PATH.read_text())


@st.cache_data(ttl=300)
def load_price_data() -> pd.DataFrame:
    frames = []
    daily_dir = BASE_DIR / "data" / "raw" / "daily"
    for csv_path in sorted(daily_dir.glob("*.csv")):
        frame = pd.read_csv(csv_path, usecols=["Date", "Adj Close"])
        frame["Date"] = pd.to_datetime(frame["Date"])
        frame = frame.rename(columns={"Adj Close": csv_path.stem}).set_index("Date")
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=1).sort_index()


def asset_category(ticker: str) -> str:
    if ticker in {"BTC-USD", "ETH-USD"}:
        return "Crypto"
    if ticker == "SPY":
        return "ETF"
    if ticker == "CDR.WA":
        return "European Equity"
    return "Equity"


def build_assets_df(payload: dict) -> pd.DataFrame:
    rows = []
    for asset in payload.get("assets", []):
        intelligence = asset.get("intelligence", {})
        recommendation = asset.get("recommendation", {})
        projection = asset.get("projection", {})
        total_return = intelligence.get("total_return", {})
        projected_range = projection.get("projected_range", {})
        rows.append(
            {
                "Ticker": asset.get("ticker"),
                "Category": asset_category(asset.get("ticker", "")),
                "Rank": intelligence.get("asset_rank"),
                "Current Price": intelligence.get("current_price"),
                "Return 30D %": total_return.get("30d"),
                "Return 1Y %": total_return.get("1y"),
                "Return 5Y %": total_return.get("5y"),
                "Volatility %": intelligence.get("annualized_volatility_pct"),
                "Drawdown %": intelligence.get("max_drawdown_pct"),
                "Sharpe": intelligence.get("sharpe_ratio"),
                "Correlation SPY": intelligence.get("correlation_with_spy"),
                "Risk Score": intelligence.get("risk_score"),
                "Opportunity Score": intelligence.get("opportunity_score"),
                "Action": recommendation.get("action"),
                "Confidence": recommendation.get("confidence"),
                "Risk Level": recommendation.get("risk_level"),
                "Rationale": recommendation.get("rationale"),
                "Key Drivers": ", ".join(recommendation.get("key_drivers", [])),
                "Trend Outlook": projection.get("trend_outlook"),
                "Projection Confidence": projection.get("projection_confidence"),
                "Projection Low": projected_range.get("low"),
                "Projection Mid": projected_range.get("mid"),
                "Projection High": projected_range.get("high"),
                "Projection Horizon Days": projection.get("projection_horizon_days"),
                "Scenario Note": projection.get("scenario_note"),
            }
        )
    return pd.DataFrame(rows).sort_values("Rank").reset_index(drop=True)


payload = load_payload()
assets_df = build_assets_df(payload) if payload else pd.DataFrame()
prices_df = load_price_data()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Portfolio copilot online. Ask for an asset analysis, a portfolio overview, or a risk explanation.",
        }
    ]

if "system_logs" not in st.session_state:
    st.session_state.system_logs = ["[SYSTEM] Frontend initialized with backend payload integration."]


def add_log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.system_logs.insert(0, f"[{timestamp}] {message}")


with st.sidebar:
    st.image(
        "https://github.com/EYAIChallenge/Overview/raw/main/EY_Logo_Beam_RGB_White_Yellow.png",
        width=84,
    )
    st.title("EY Portfolio Copilot")
    api_key = st.text_input("OpenAI API Key", type="password", help="Used by the chat agent.")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("Chat agent ready")
    else:
        st.warning("Add an API key to enable the chat agent")

    st.markdown("### Data status")
    if payload:
        st.write(f"Payload updated: `{payload.get('generated_at', 'unknown')}`")
        st.write(f"Assets loaded: `{payload.get('portfolio_summary', {}).get('asset_count', 0)}`")
    else:
        st.error("Missing outputs/frontend_payload.json")

    selected_asset = st.selectbox(
        "Focus asset",
        assets_df["Ticker"].tolist() if not assets_df.empty else available_assets(),
        index=0 if assets_df.empty else min(1, len(assets_df) - 1),
    )

st.title("Vector Alpha — Investment Decision Support Platform")
st.caption("AI-powered portfolio intelligence for opportunity discovery, risk mitigation, and model-based scenario projection.")

if not payload or assets_df.empty:
    st.error("Backend payload not found. Run `python src/build_frontend_payload.py` first.")
    st.stop()

selected_row = assets_df.loc[assets_df["Ticker"] == selected_asset].iloc[0]
portfolio_summary = payload.get("portfolio_summary", {})

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Focus Asset", selected_asset, f"Rank #{int(selected_row['Rank'])}")
col2.metric("5Y Return", f"{selected_row['Return 5Y %']:.2f}%", f"30D {selected_row['Return 30D %']:.2f}%")
col3.metric("Volatility", f"{selected_row['Volatility %']:.2f}%", selected_row["Risk Level"])
col4.metric("Recommendation", selected_row["Action"].upper(), selected_row["Confidence"])
col5.metric("Projection", selected_row["Trend Outlook"].upper(), f"{int(selected_row['Projection Horizon Days'])} days")

st.markdown("---")

tab_overview, tab_asset, tab_risk, tab_chat, tab_invest, tab_logs = st.tabs(
    ["Portfolio Overview", "Asset Drilldown", "Risk Map", "AI Copilot", "Invest Capital", "System Logs"]
)

with tab_overview:
    left, right = st.columns([1, 1])
    with left:
        category_view = (
            assets_df.groupby("Category")["Opportunity Score"]
            .mean()
            .reset_index()
            .rename(columns={"Opportunity Score": "Average Opportunity Score"})
        )
        fig = px.pie(
            category_view,
            names="Category",
            values="Average Opportunity Score",
            hole=0.45,
            title="Investment universe by category signal",
        )
        fig.update_layout(template="plotly_dark", height=380)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Portfolio Summary")
        st.write(f"Top opportunities: `{', '.join(portfolio_summary.get('top_opportunities', []))}`")
        st.write(f"Highest risk assets: `{', '.join(portfolio_summary.get('highest_risk_assets', []))}`")
        st.write(f"Diversification candidates: `{', '.join(portfolio_summary.get('diversification_candidates', []))}`")
        st.write(f"Average opportunity score: `{portfolio_summary.get('average_opportunity_score', 'n/a')}`")
        st.write(f"Average risk score: `{portfolio_summary.get('average_risk_score', 'n/a')}`")

    st.subheader("Asset Ranking Table")
    st.dataframe(
        assets_df[
            [
                "Ticker",
                "Category",
                "Rank",
                "Action",
                "Confidence",
                "Return 5Y %",
                "Volatility %",
                "Risk Score",
                "Opportunity Score",
                "Trend Outlook",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with tab_asset:
    asset_payload = get_payload_asset(selected_asset)
    if not asset_payload:
        st.warning("No asset payload available.")
    else:
        left, right = st.columns([1.1, 0.9])
        with left:
            st.subheader(f"{selected_asset} historical performance")
            if selected_asset in prices_df.columns:
                chart_df = prices_df[[selected_asset]].dropna().reset_index()
                chart_df["Normalized"] = chart_df[selected_asset] / chart_df[selected_asset].iloc[0] * 100
                fig = px.line(chart_df, x="Date", y="Normalized", title=f"{selected_asset} normalized price (base 100)")
                fig.update_layout(template="plotly_dark", height=360)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Historical series not available for chart.")

            projection_df = pd.DataFrame(
                {
                    "Scenario": ["Low", "Mid", "High"],
                    "Projected Price": [
                        selected_row["Projection Low"],
                        selected_row["Projection Mid"],
                        selected_row["Projection High"],
                    ],
                }
            )
            fig = px.bar(
                projection_df,
                x="Scenario",
                y="Projected Price",
                color="Scenario",
                title=f"{selected_asset} model-based scenario projection",
            )
            fig.update_layout(template="plotly_dark", height=320, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("Recommendation")
            st.metric("Action", selected_row["Action"].upper(), selected_row["Confidence"])
            st.write(selected_row["Rationale"])
            st.write(f"Key drivers: `{selected_row['Key Drivers']}`")

            st.subheader("Projection")
            st.write(f"Trend outlook: `{selected_row['Trend Outlook']}`")
            st.write(f"Projection confidence: `{selected_row['Projection Confidence']}`")
            st.write(f"Projected range: `{selected_row['Projection Low']}` to `{selected_row['Projection High']}`")
            st.write(selected_row["Scenario Note"])

            st.subheader("Core metrics")
            metric_table = pd.DataFrame(
                {
                    "Metric": [
                        "Return 30D %",
                        "Return 1Y %",
                        "Return 5Y %",
                        "Volatility %",
                        "Drawdown %",
                        "Sharpe",
                        "Correlation SPY",
                        "Risk Score",
                        "Opportunity Score",
                    ],
                    "Value": [
                        selected_row["Return 30D %"],
                        selected_row["Return 1Y %"],
                        selected_row["Return 5Y %"],
                        selected_row["Volatility %"],
                        selected_row["Drawdown %"],
                        selected_row["Sharpe"],
                        selected_row["Correlation SPY"],
                        selected_row["Risk Score"],
                        selected_row["Opportunity Score"],
                    ],
                }
            )
            st.dataframe(metric_table, use_container_width=True, hide_index=True)

with tab_risk:
    left, right = st.columns([1, 1])
    with left:
        fig = px.scatter(
            assets_df,
            x="Volatility %",
            y="Return 5Y %",
            color="Action",
            size="Opportunity Score",
            text="Ticker",
            hover_data=["Risk Score", "Sharpe", "Trend Outlook"],
            title="Risk vs return",
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(template="plotly_dark", height=430)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        corr_df = pd.DataFrame(payload.get("correlation_matrix", {})).sort_index()
        fig = px.imshow(
            corr_df,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Correlation matrix",
        )
        fig.update_layout(template="plotly_dark", height=430)
        st.plotly_chart(fig, use_container_width=True)

with tab_chat:
    st.subheader("AI Copilot")
    st.caption("This chat uses the same CSV files and frontend payload that power the dashboard.")

    chat_container = st.container(height=360)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ask about AAPL, BTC-USD, risk, projections, or the whole portfolio"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        add_log(f"Agent request: {prompt[:60]}")
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("Add your OpenAI API key in the sidebar to enable the copilot.")
                else:
                    try:
                        response = financial_agent.invoke(prompt)
                        content = response["output"]
                        st.markdown(content)
                        st.session_state.messages.append({"role": "assistant", "content": content})
                        add_log("Agent response delivered successfully.")
                    except Exception as error:
                        st.error(f"Agent error: {error}")
                        add_log(f"Agent error: {error}")

    with st.expander("Backend context snapshot"):
        st.code(format_portfolio_analysis(), language="text")

with tab_invest:
    st.subheader("Capital Allocation Simulator")
    st.caption("Use the real portfolio analytics to test how new capital could be deployed.")

    col_inv1, col_inv2, col_inv3 = st.columns([1.4, 1.2, 1])
    with col_inv1:
        new_capital = st.number_input(
            "New capital to invest ($)",
            min_value=1000,
            value=50000,
            step=5000,
            key="new_capital",
        )
    with col_inv2:
        invest_asset = st.selectbox(
            "Preferred asset",
            assets_df["Ticker"].tolist(),
            key="invest_asset",
        )
    with col_inv3:
        st.markdown("<br>", unsafe_allow_html=True)
        execute_investment = st.button("Simulate Allocation", type="primary")

    invest_row = assets_df.loc[assets_df["Ticker"] == invest_asset].iloc[0]

    score = max(0, min(100, round(float(invest_row["Opportunity Score"]) - 0.35 * float(invest_row["Risk Score"]) + 25, 1)))
    if score >= 75:
        score_label = "Attractive"
        score_delta = "Favorable setup"
    elif score >= 55:
        score_label = "Balanced"
        score_delta = "Selective entry"
    else:
        score_label = "Cautious"
        score_delta = "Risk elevated"

    st.markdown("---")
    met1, met2, met3, met4, met5 = st.columns(5)
    met1.metric("Expected profile", invest_row["Trend Outlook"].upper(), invest_row["Projection Confidence"])
    met2.metric("ROI (1Y)", f"{invest_row['Return 1Y %']:.2f}%")
    met3.metric("5Y Return", f"{invest_row['Return 5Y %']:.2f}%")
    met4.metric("Volatility", f"{invest_row['Volatility %']:.2f}%", invest_row["Risk Level"])
    met5.metric("Final Score", f"{score:.1f}/100", score_delta)

    if execute_investment:
        estimated_units = new_capital / float(invest_row["Current Price"]) if float(invest_row["Current Price"]) else 0
        st.success(
            f"Simulation ready: allocating ${new_capital:,.0f} to {invest_asset} buys approximately {estimated_units:,.2f} units."
        )
        add_log(f"Investment simulation created for {invest_asset} with ${new_capital:,.0f}.")

    left, right = st.columns([1, 1])
    with left:
        scenario_df = pd.DataFrame(
            {
                "Scenario": ["Low", "Mid", "High"],
                "Projected Price": [
                    invest_row["Projection Low"],
                    invest_row["Projection Mid"],
                    invest_row["Projection High"],
                ],
            }
        )
        fig = px.bar(
            scenario_df,
            x="Scenario",
            y="Projected Price",
            color="Scenario",
            title=f"{invest_asset} scenario projection for capital deployment",
        )
        fig.update_layout(template="plotly_dark", height=340, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Allocation view")
        st.write(f"Recommended action: `{invest_row['Action']}`")
        st.write(f"Confidence: `{invest_row['Confidence']}`")
        st.write(f"Risk / Opportunity: `{invest_row['Risk Score']}` / `{invest_row['Opportunity Score']}`")
        st.write(f"Scenario note: {invest_row['Scenario Note']}")
        st.write(f"Key drivers: `{invest_row['Key Drivers']}`")

    st.markdown("### Ask the copilot about this allocation")
    if "invest_messages" not in st.session_state:
        st.session_state.invest_messages = [
            {
                "role": "assistant",
                "content": "Tell me how much capital you want to allocate and your objective, and I will reason using the real portfolio analytics.",
            }
        ]

    invest_chat_container = st.container(height=260)
    with invest_chat_container:
        for message in st.session_state.invest_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if invest_prompt := st.chat_input(
        "Example: Should I allocate the new capital to AAPL or BTC-USD given the current risk profile?",
        key="invest_chat_input",
    ):
        st.session_state.invest_messages.append({"role": "user", "content": invest_prompt})
        add_log(f"Investment copilot request: {invest_prompt[:60]}")
        with invest_chat_container:
            with st.chat_message("user"):
                st.markdown(invest_prompt)
            with st.chat_message("assistant"):
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("Add your OpenAI API key in the sidebar to enable the copilot.")
                else:
                    try:
                        enriched_prompt = (
                            f"I have ${new_capital:,.0f} to invest and I am evaluating {invest_asset}. "
                            f"Use the portfolio analytics and recommendation engine to advise me. "
                            f"Original question: {invest_prompt}"
                        )
                        response = financial_agent.invoke(enriched_prompt)
                        content = response["output"]
                        st.markdown(content)
                        st.session_state.invest_messages.append({"role": "assistant", "content": content})
                        add_log("Investment copilot response delivered successfully.")
                    except Exception as error:
                        st.error(f"Agent error: {error}")
                        add_log(f"Investment copilot error: {error}")

with tab_logs:
    st.code("\n".join(st.session_state.system_logs), language="bash")
