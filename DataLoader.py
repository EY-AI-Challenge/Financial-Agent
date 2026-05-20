import os

import numpy as np
import pandas as pd
import yfinance as yf

from Config import STOCKS, START_DATE, END_DATE


# ── helpers ──────────────────────────────────────────────────────────────────

def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _bollinger(series: pd.Series, period=20, std=2):
    ma = series.rolling(period).mean()
    sd = series.rolling(period).std()
    return ma + std * sd, ma, ma - std * sd


# ── main loader ───────────────────────────────────────────────────────────────

def load_stock(ticker: str, start: str = START_DATE, end: str = END_DATE) -> pd.DataFrame:
    raw = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)

    if raw.empty:
        raise ValueError(f"Sem dados para {ticker} entre {start} e {end}")

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]
    df.index = pd.to_datetime(df.index)
    df = df.dropna(subset=["close"])

    close = df["close"]

    df["return_1d"]    = close.pct_change()
    df["return_5d"]    = close.pct_change(5)
    df["ma_20"]        = close.rolling(20).mean()
    df["ma_50"]        = close.rolling(50).mean()
    df["rsi_14"]       = _rsi(close, 14)
    df["macd"], df["macd_signal"], df["macd_hist"] = _macd(close)
    df["bb_upper"], df["bb_mid"], df["bb_lower"]   = _bollinger(close, 20)
    df["volatility_20"] = df["return_1d"].rolling(20).std()
    df["ticker"]       = ticker

    df = df.dropna(subset=["ma_50", "rsi_14", "macd"])
    return df


def load_all(tickers: list = STOCKS, start: str = START_DATE, end: str = END_DATE) -> dict:
    data = {}
    for ticker in tickers:
        try:
            data[ticker] = load_stock(ticker, start, end)
            print(f"[OK] {ticker}: {len(data[ticker])} linhas")
        except Exception as e:
            print(f"[ERRO] {ticker}: {e}")
    return data


def merge_all(data: dict) -> pd.DataFrame:
    frames = list(data.values())
    if not frames:
        raise ValueError("Nenhum dado carregado")
    return pd.concat(frames).sort_index()


# ── export para CSV ───────────────────────────────────────────────────────────

def save_csv(data: dict, folder: str = "data") -> None:
    """
    Guarda um CSV por ticker em data/AAPL.csv, data/MSFT.csv, etc.
    Também guarda um ficheiro combinado data/all_stocks.csv.
    """
    os.makedirs(folder, exist_ok=True)

    for ticker, df in data.items():
        path = os.path.join(folder, f"{ticker}.csv")
        df.to_csv(path)
        print(f"[SAVED] {path}")

    merged = merge_all(data)
    merged_path = os.path.join(folder, "all_stocks.csv")
    merged.to_csv(merged_path)
    print(f"[SAVED] {merged_path}  ({len(merged)} linhas no total)")


def load_from_csv(folder: str = "data", tickers: list = STOCKS) -> dict:
    """
    Carrega os CSVs já guardados em vez de ir buscar à API.
    Útil para não depender de internet durante a demo.
    """
    data = {}
    for ticker in tickers:
        path = os.path.join(folder, f"{ticker}.csv")
        if os.path.exists(path):
            data[ticker] = pd.read_csv(path, index_col=0, parse_dates=True)
            print(f"[LOADED] {path}")
        else:
            print(f"[AVISO] {path} não encontrado — corre save_csv() primeiro")
    return data


# ── análise de correlação (útil para apresentação) ────────────────────────────

def correlation_matrix(data: dict, on: str = "return_1d") -> pd.DataFrame:
    """
    Matriz de correlação entre tickers.

    Parâmetros
    ----------
    data : dicionário {ticker: DataFrame} devolvido por load_all().
    on   : coluna a correlacionar — 'return_1d' (default, mais correcto
           estatisticamente) ou 'close' (mais visual para apresentação).

    Retorna
    -------
    DataFrame NxN com correlações de Pearson.
    """
    series = {ticker: df[on] for ticker, df in data.items()}
    combined = pd.DataFrame(series).dropna()
    corr = combined.corr()
    print(f"\nCorrelação de '{on}' entre {list(data.keys())}:")
    print(corr.round(2))
    return corr



SECTORES = {
    "Tech":      ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
    "Consumo":   ["AMZN", "TSLA"],
    "Financeiro": ["JPM", "V"],
    "Saúde":     ["UNH"],
}

def correlation_sectores(data: dict, sectores: dict = SECTORES) -> pd.DataFrame:
    """
    Correlação entre sectores — cada sector é a média dos retornos diários das suas empresas.
    """
    series = {}
    for sector, tickers in sectores.items():
        tickers_disponiveis = [t for t in tickers if t in data]
        returns = pd.concat([data[t]["return_1d"] for t in tickers_disponiveis], axis=1)
        series[sector] = returns.mean(axis=1)

    corr = pd.DataFrame(series).dropna().corr()
    print("\nCorrelação entre sectores:")
    print(corr.round(2))
    return corr


def summary(data: dict) -> pd.DataFrame:
    """
    Tabela resumo por ticker: período, nº de dias, retorno total,
    volatilidade anualizada e RSI médio. Boa para mostrar na apresentação.
    """
    rows = []
    for ticker, df in data.items():
        ret_total = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
        vol_anual = df["return_1d"].std() * np.sqrt(252) * 100
        rows.append({
            "ticker":        ticker,
            "início":        df.index[0].date(),
            "fim":           df.index[-1].date(),
            "dias":          len(df),
            "retorno_%":     round(ret_total, 1),
            "volatilidade_%": round(vol_anual, 1),
            "rsi_médio":     round(df["rsi_14"].mean(), 1),
        })
    tbl = pd.DataFrame(rows).set_index("ticker")
    print("\n── Resumo do Portfolio ──────────────────────────────────")
    print(tbl.to_string())
    return tbl



# ── execução directa ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import seaborn as sns

    print("A descarregar dados...")
    data = load_all()
    save_csv(data)

    # resumo geral — bom para mostrar no ecrã durante a apresentação
    summary(data)

    # correlação entre retornos diários (optional charts — needs seaborn)
    corr = correlation_matrix(data, on="return_1d")
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("Correlação entre Retornos Diários")
    plt.tight_layout()
    plt.show()

    corr_sec = correlation_sectores(data)

    plt.figure(figsize=(6, 5))
    sns.heatmap(corr_sec, annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("Correlação entre Sectores")
    plt.tight_layout()
    plt.show()