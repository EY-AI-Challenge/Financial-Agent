import os

# ── stocks e datas ────────────────────────────────────────────────────────────
STOCKS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "V", "UNH"]
START_DATE = "2013-01-01"
END_DATE   = "2024-12-31"
DATA_FOLDER = "data"  # CSV folder used by tools and Streamlit (offline demo)

# ── portfolio simulado ────────────────────────────────────────────────────────
INITIAL_CAPITAL = 100_000  # euros

# ── agente de decisão ─────────────────────────────────────────────────────────
DECISION_MODEL   = "RandomForestClassifier"  # model.ipynb: direction = return_1d > 0
MAX_TREE_DEPTH   = 5
RANDOM_STATE     = 42
CONFIDENCE_THRESHOLD = 0.65   # minimum probability to trust ML signal (else HOLD)
MODEL_PATH       = "models/decision_model.pkl"

# ── agente de qualidade ───────────────────────────────────────────────────────
LLM_MODEL        = "gemma4:e2b"
QUALITY_SCORE_MIN = 7          # score mínimo (0-10) para aprovar decisão
MAX_RETRIES       = 3          # máximo de tentativas antes de desistir

# ── API keys (lê das variáveis de ambiente — nunca colocar a key em texto aqui)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── indicadores técnicos (usados em data_loader.py) ──────────────────────────
RSI_PERIOD     = 14
MACD_FAST      = 12
MACD_SLOW      = 26
MACD_SIGNAL    = 9
BB_PERIOD      = 20
MA_SHORT       = 20
MA_LONG        = 50
VOLATILITY_WIN = 20

# ── thresholds de sinal ───────────────────────────────────────────────────────
RSI_OVERSOLD    = 30   # abaixo → possível BUY
RSI_OVERBOUGHT  = 70   # acima  → possível SELL