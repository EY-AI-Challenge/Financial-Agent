![alt text](https://github.com/EYAIChallenge/Overview/blob/main/Banner-EY-1280x640.jpg "EY AI Challenge")

<h1 align="center"> <img src="https://github.com/EYAIChallenge/Overview/blob/main/EY_Logo_Beam_RGB_White_Yellow.png" width="40" alt="Logo"/> AI Challenge 2026 | Financial Agent Challenge </h1>

---

## 📊 Description

In this challenge, your team will act as strategic consultants for a sophisticated **investment fund** seeking to leverage **AI** in its daily operations. The fund manages a **diverse portfolio** of 11 different stocks and cryptocurrencies. Your team can choose to focus on the entire portfolio, a strategic selection, or an in-depth analysis of a single high-value asset.

### **Objective**  
Your mission is to create a **decision support platform** that transforms the fund's investment capabilities. Whether designing an intelligent trading agent, a sophisticated analytical dashboard, or a hybrid solution, you must demonstrate how AI can generate **tangible business value** in financial markets.

---

## 💡 Data

The dataset includes **historical financial data** from different assets, for example: 
- **Stocks:** AMZN, AAPL, GOOGL, MSFT, UDMY, NXE, SPY, CDR.WA, EH  
- **Cryptocurrencies:** BTC-USD, ETH-USD  

All data is from Yahoo library (yfinance) stored in `.csv` files. 

### Data Columns:
- **Datetime / Date:** Timestamp of the market data entry (hourly or daily).
- **Close:** Price at the end of the interval.
- **High:** Highest price during the interval.
- **Low:** Lowest price during the interval.
- **Open:** Price at the beginning of the interval.
- **Volume:** Number of shares/contracts/units traded.

---

## 🎯 Consulting Mindset Expectations

- **Strategic Advisors:** Position yourselves as trusted advisors who understand both **technology** and **financial markets**. Balance technical innovation with practical considerations.
- **Value Architects:** Articulate how your solution creates **measurable business impact**.
- **Sell the Solution, Not Just the Process:** Present your solution as a **valuable asset**, highlighting **business impact** and suggesting **clear next steps**.

---

## 📦 Deliverables

- ✅ A working prototype of your solution
- ✅ Organized and well-documented code, that can be reproducible
- ✅ A strategic presentation pitching your solution to the judging panel as if they were the client's executive stakeholders
- ✅ A technical presentation pitching your solution to the judging panel as if they were the client's IT stakeholders
- ✅ A frontend for the solution is mandatory for the live demo of the strategic presentation

🔹 **Optional Enhancements**:  
- Performance analysis vs traditional knowledge access methods

<h2 align="center"> ⚠️ **Important Submission Requirement** ⚠️ </h2>
<h3> ✅ Before the 14h00 deadline</h3>

Submit you solution to your specific branch:
- Repository with the code of the solution developed
  - The solution must be ready to run
- A README file with the context of the solution and how to run it

---

## 💡 Tips for Competitors

- **Master the Market Data**: Dive deep into the stock and cryptocurrency data. Look for patterns, correlations, and anomalies that could inform **strategic investment decisions**.
- **Develop a Clear Value Proposition**: Define exactly how your solution will add value - whether by **improving decision speed**, **reducing risk**, **identifying overlooked opportunities**, or **enhancing portfolio performance**.
- **Think Like the Client**: Understand the day-to-day of **investment professionals**. What insights would improve their decisions? How can your solution seamlessly integrate into their workflow?
- **Establish a Performance Framework**: Use metrics like **ROI**, **risk-adjusted returns**, **prediction accuracy**, and compare against market benchmarks.
- **Embrace Innovation with Purpose**: Ensure innovations directly address the fund's business goals. Every feature should contribute to strategic value.
- **Craft a Business Case**: When presenting, articulate not only the **technical** details but also the **financial** impact of your solution. Be ready to defend your approach.

---

## 🛠️ Tech & Tools

- **Mandatory:**  
  - Solution must be developed mainly using Python  
  - You'll publish the solution into a specific branch of the challenge's repository

- **Free to Choose:**  
  - Libraries/Packages
  - Visualization
  - Frontend solution
  - AI Assistants

---

## ⏱️ Time Management & Rules

- Total Time: **4 hours** – No extensions  
- Final Presentations: **5 minutes each** – Simulate a client-facing pitch
  - You must divide the team for the strategic and technical presentations
- Support:
  - 🧑‍💻 1 technical session (max 5 minutes)  
  - 💼 1 business session (max 5 minutes)  
  - **Note:** Assistants guide only — no direct solutions

---

## 📋 Strategy & Workflow Tips

1. **Assign Roles Early** — e.g., data analyst, business strategist, presenter  
2. **Work in Parallel** — Divide and conquer  
3. **Start the Presentation Early** — Don’t wait until the last 10 minutes  
4. **Be Realistic** — Focused and clear beats complex and incomplete  

💡 **Pro Tip:**  
Judging includes **teamwork**, **structure**, and **communication**, not just technical quality

---

## 💬 Final Thought

This challenge invites you to bridge the worlds of **cutting-edge AI technology** and **sophisticated financial strategy**.

🏆 The most successful teams will demonstrate not just technical prowess,  
but the ability to **translate that technology into meaningful business advantage**.

> You are developing more than just a tool –  
> you are creating a **strategic asset** that could fundamentally enhance how investment decisions are made.

---

## BigBuck5 — Our Solution

**BigBuck5** is an AI **decision-support** platform for an investment fund. It analyses US equities using historical market data and rule-based signals (RSI). It does **not** execute trades.

### Architecture

```
DataLoader.py  →  data/all_stocks.csv  →  decision_engine.py (model.ipynb: RF classifier + regressor)
                                      ↓
                               tools.py  →  agent.py (LangGraph + Ollama)  →  app.py (Streamlit)
```

### Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Python 3.10+** | Tested on 3.11 / 3.14 |
| **Ollama** | [ollama.com](https://ollama.com) — must be running during chat |
| **Internet** | Only for the first `DataLoader.py` run (downloads CSVs) |

Default LLM model in code: `gemma4:e2b`. Change in the Streamlit sidebar or in `agent.py` if you use another model (`ollama pull <model>`).

### Installation

```bash
cd Financial-Agent
pip install -r requirements.txt
```

This installs: `pandas`, `numpy`, `yfinance`, `scikit-learn`, `joblib`, `langgraph`, `langchain-core`, `langchain-ollama`, `streamlit`.

### Run the app (recommended for demo)

**Step 1 — Download market data (once, needs internet):**

```bash
python DataLoader.py
```

Creates `data/AAPL.csv`, `data/MSFT.csv`, etc. (10 US stocks in `Config.STOCKS`).

**Step 2 — Train the ML model (once, or after new data):**

```bash
python decision_engine.py
```

Saves `models/decision_model.pkl` (classifier: up/down from `return_1d`; regressor: close price — same as `model.ipynb`). The agent uses this for `get_trading_signal` (auto-trains on first use if missing).

**Step 3 — Start Ollama** (desktop app or `ollama serve`).

**Step 4 — Launch the UI:**

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Use the sidebar for charts and example questions.

**Alternative — terminal chat only:**

```bash
python agent.py
```

### Project files

| File | Role |
|------|------|
| `Config.py` | Stocks list, dates, RSI thresholds |
| `DataLoader.py` | Download data + technical indicators → CSV |
| `decision_engine.py` | RandomForest ML model (train + predict) |
| `tools.py` | Market tools (summary, ML signal, compare, calculator) |
| `agent.py` | LangGraph agent + Ollama |
| `prompts.py` | System prompt for the fund assistant |
| `app.py` | Streamlit frontend |
| `requirements.txt` | Python dependencies |

### Example demo questions

- *What is the trading signal for AAPL?*
- *Give me a technical summary of MSFT*
- *Compare AAPL, MSFT and GOOGL*

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `No CSV data` in the UI | Run `python DataLoader.py` |
| `Could not start agent` | Start Ollama; check model name with `ollama list` |
| `streamlit` not found | `pip install streamlit` or `python -m streamlit run app.py` |
| Garbled text with `$` in answers | Fixed in latest version — use **USD** format; clear chat in sidebar |
| Slow first reply | Normal — LLM + tool calls on first question |

### Supported stocks (no crypto in this build)

`AAPL`, `MSFT`, `AMZN`, `GOOGL`, `META`, `TSLA`, `NVDA`, `JPM`, `V`, `UNH`

---

### 🏁 Brought to you by **EY AI Challenge**
