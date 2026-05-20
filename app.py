"""
Streamlit UI for the BigBuck5 financial agent.
Run: streamlit run app.py
"""

import os
import re

import pandas as pd
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from Config import DATA_FOLDER, STOCKS
from agent import create_agent

# ── Theme (custom CSS) ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BigBuck5 | Financial Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Main background */
    .stApp {
        background: linear-gradient(165deg, #0f1419 0%, #1a2332 45%, #0f1419 100%);
    }

    /* Header hero */
    .bb5-hero {
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 50%, #1e3a5f 100%);
        border: 1px solid rgba(255, 200, 87, 0.25);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35);
    }
    .bb5-hero h1 {
        color: #ffc857 !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        font-family: 'Segoe UI', system-ui, sans-serif !important;
    }
    .bb5-hero p {
        color: #b8c5d6 !important;
        margin: 0.35rem 0 0 0 !important;
        font-size: 0.95rem !important;
    }

    /* Signal badges */
    .signal-badge {
        display: inline-block;
        padding: 0.35rem 1rem;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
        color: #0f1419 !important;
    }
    .signal-BUY { background: #22c55e !important; }
    .signal-SELL { background: #ef4444 !important; color: #fff !important; }
    .signal-HOLD { background: #f59e0b !important; }

    /* Section cards in assistant replies */
    .bb5-section {
        background: rgba(30, 45, 65, 0.85);
        border-left: 4px solid #ffc857;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin: 0.65rem 0;
        font-family: 'Segoe UI', system-ui, sans-serif !important;
        font-size: 0.95rem !important;
        line-height: 1.55 !important;
        color: #e8eef4 !important;
    }
    .bb5-section-title {
        color: #ffc857 !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem !important;
    }
    .bb5-disclaimer {
        border-left-color: #6b7280 !important;
        font-size: 0.85rem !important;
        color: #9ca3af !important;
        font-style: italic;
    }

    /* Chat messages — consistent sans-serif */
    [data-testid="stChatMessage"] {
        font-family: 'Segoe UI', system-ui, sans-serif !important;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {
        font-family: 'Segoe UI', system-ui, sans-serif !important;
        line-height: 1.55 !important;
    }

    /* Sidebar polish */
    [data-testid="stSidebar"] {
        background: #151c28 !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffc857 !important;
        font-family: 'Segoe UI', system-ui, sans-serif !important;
    }

    /* Example buttons */
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 8px;
        border: 1px solid rgba(255, 200, 87, 0.35);
        background: rgba(30, 58, 95, 0.6);
        color: #e8eef4;
        font-size: 0.82rem;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        border-color: #ffc857;
        background: rgba(45, 90, 135, 0.8);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="bb5-hero">
        <h1>BigBuck5 — Investment Decision Support</h1>
        <p>AI assistant for fund managers · powered by local market data (CSV)</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Text formatting helpers ───────────────────────────────────────────────────

_SIGNAL_RE = re.compile(r"\b(BUY|SELL|HOLD)\b", re.IGNORECASE)
_HEADER_RE = re.compile(
    r"^\s*(?:\d+\.\s*)?(?:\*\*)?([\w\s]+?)(?:\*\*)?\s*[—\-:]+\s*(.*)$",
    re.IGNORECASE,
)


def _escape_markdown(text: str) -> str:
    """Prevent $ from triggering LaTeX math mode in Streamlit markdown."""
    return text.replace("$", "\\$")


def _extract_signal(text: str) -> str | None:
    match = _SIGNAL_RE.search(text)
    return match.group(1).upper() if match else None


def _plain_to_html(text: str) -> str:
    """Convert simple markdown to HTML for section cards."""
    text = _escape_markdown(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = text.replace("\n", "<br>")
    return text


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split assistant text into (title, body) by section headers."""
    text = text.strip()
    if not text:
        return []

    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in text.split("\n"):
        m = _HEADER_RE.match(line)
        if m:
            if current_title is not None:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append((current_title, body))
            current_title = m.group(1).strip()
            first_line = m.group(2).strip()
            current_lines = [first_line] if first_line else []
        else:
            current_lines.append(line)

    if current_title is not None:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_title, body))
    elif current_lines:
        sections.append(("Answer", "\n".join(current_lines).strip()))

    return sections if sections else [("Answer", text)]


def _render_assistant_message(text: str) -> None:
    """Render formatted assistant reply with signal badge and section cards."""
    signal = _extract_signal(text)
    if signal:
        st.markdown(
            f'<span class="signal-badge signal-{signal}">{signal}</span>',
            unsafe_allow_html=True,
        )

    sections = _split_sections(text)

    if len(sections) <= 1 and sections[0][0] == "Answer":
        # Plain fallback — escape $ and use markdown
        st.markdown(_escape_markdown(text))
        return

    for title, body in sections:
        title_lower = title.lower()
        extra_class = " bb5-disclaimer" if "disclaimer" in title_lower else ""
        # Clean body: fix glued words from old $-math bugs
        body = re.sub(r"(\d+\.\d{2})([a-zA-Záàâãéèêíóôõúç])", r"\1 \2", body, flags=re.I)
        body_html = _plain_to_html(body)
        st.markdown(
            f'<div class="bb5-section{extra_class}">'
            f'<div class="bb5-section-title">{title}</div>'
            f"<div>{body_html}</div></div>",
            unsafe_allow_html=True,
        )


# ── Data helpers ──────────────────────────────────────────────────────────────

def _data_ready() -> bool:
    if not os.path.isdir(DATA_FOLDER):
        return False
    return any(
        os.path.exists(os.path.join(DATA_FOLDER, f"{t}.csv")) for t in STOCKS
    )


def _load_chart_df(ticker: str, days: int = 60) -> pd.DataFrame | None:
    path = os.path.join(DATA_FOLDER, f"{ticker}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    if "close" not in df.columns:
        return None
    subset = df[["close"]].tail(days)
    subset.index = pd.to_datetime(subset.index)
    return subset


def ask_agent(agent, question: str, thread_id: str) -> tuple[str, list[str]]:
    config = {"configurable": {"thread_id": thread_id}}
    state = {"messages": [HumanMessage(content=question)]}
    answer = ""
    status_log: list[str] = []

    for event in agent.app.stream(state, config=config):
        for node, payload in event.items():
            if node == "tools":
                status_log.append("Fetched market data from CSV")
            elif node == "BigBuck5":
                msg = payload["messages"][-1]
                if isinstance(msg, AIMessage):
                    if getattr(msg, "tool_calls", None):
                        names = [tc.get("name", "?") for tc in msg.tool_calls]
                        status_log.append(f"Calling tools: {', '.join(names)}")
                    elif msg.content:
                        answer = msg.content
            elif node == "quality_control":
                status_log.append("Quality check ran")

    return answer, status_log


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Settings")
    model_name = st.text_input("Ollama model", value="gemma4:e2b")
    thread_id = st.text_input("Conversation id", value="streamlit_demo")

    st.divider()
    st.subheader("Market chart")

    available = [
        t for t in STOCKS
        if os.path.exists(os.path.join(DATA_FOLDER, f"{t}.csv"))
    ] or list(STOCKS)

    chart_ticker = st.selectbox("Ticker", available, index=0)
    chart_days = st.slider("Days shown", 30, 252, 60)

    if _data_ready() and chart_ticker:
        chart_df = _load_chart_df(chart_ticker, chart_days)
        if chart_df is not None:
            st.line_chart(chart_df, height=220)
            last_close = chart_df["close"].iloc[-1]
            st.metric("Last close", f"USD {last_close:.2f}")
        else:
            st.warning(f"No chart data for {chart_ticker}")
    else:
        st.error("No CSV data. Run: python DataLoader.py")

    st.divider()
    st.subheader("Quick questions")
    examples = [
        "What is the trading signal for AAPL?",
        "Give me a technical summary of MSFT",
        "Compare AAPL, MSFT and GOOGL",
        "Which stocks are available?",
    ]
    for ex in examples:
        if st.button(ex, key=ex, use_container_width=True):
            st.session_state["pending_question"] = ex

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ── Main chat ─────────────────────────────────────────────────────────────────

col_chat, col_hint = st.columns([4, 1])

with col_hint:
    st.markdown(
        """
        <div style="
            background: rgba(30,45,65,0.6);
            border-radius: 8px;
            padding: 0.75rem;
            font-size: 0.8rem;
            color: #9ca3af;
            line-height: 1.4;
        ">
        <strong style="color:#ffc857;">Tips</strong><br>
        • Ask for signals or summaries<br>
        • Data from local CSVs<br>
        • Ollama must be running
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_chat:
    if not _data_ready():
        st.warning("Run `python DataLoader.py` then refresh this page.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "agent" not in st.session_state:
        st.session_state.agent = None
        st.session_state.agent_model = None

    if st.session_state.agent_model != model_name:
        try:
            st.session_state.agent = create_agent(model_name=model_name, use_qc=False)
            st.session_state.agent_model = model_name
        except Exception as e:
            st.session_state.agent = None
            st.error(f"Could not start agent (is Ollama running?): {e}")

    for role, content in st.session_state.messages:
        with st.chat_message(role):
            if role == "assistant":
                _render_assistant_message(content)
            else:
                st.markdown(content)

    prompt = st.chat_input("Ask about stocks, signals, or comparisons...")
    if st.session_state.get("pending_question"):
        prompt = st.session_state.pop("pending_question")

    if prompt:
        st.session_state.messages.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if st.session_state.agent is None:
                reply = "Agent not available. Check Ollama and the model name in the sidebar."
                st.error(reply)
            elif not _data_ready():
                reply = "Cannot answer: no CSV data. Run DataLoader.py first."
                st.warning(reply)
            else:
                with st.spinner("Analysing market data..."):
                    try:
                        reply, steps = ask_agent(
                            st.session_state.agent, prompt, thread_id
                        )
                        if steps:
                            with st.expander("Behind the scenes", expanded=False):
                                for s in steps:
                                    st.markdown(f"- {s}")
                        if not reply:
                            reply = (
                                "No text answer was generated. "
                                "Try rephrasing or check the Ollama model."
                            )
                    except Exception as e:
                        reply = f"Error: {e}"
                        st.exception(e)

            _render_assistant_message(reply)

        st.session_state.messages.append(("assistant", reply))
