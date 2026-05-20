import pandas as pd
import ta

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona RSI e MACD ao DataFrame de preços.
    Espera colunas: Open, High, Low, Close
    """

    # garantir colunas necessárias
    df = df[['Open', 'High', 'Low', 'Close']].copy()

    # ================= RSI =================
    df['RSI'] = ta.momentum.RSIIndicator(
        close=df['Close'],
        window=14
    ).rsi()

    # ================= MACD =================
    macd = ta.trend.MACD(
        close=df['Close'],
        window_slow=26,
        window_fast=12,
        window_sign=9
    )

    df['MACD'] = macd.macd()
    df['MACD_SIGNAL'] = macd.macd_signal()
    df['MACD_HIST'] = macd.macd_diff()

    return df 
