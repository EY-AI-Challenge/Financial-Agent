import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots
import os
import sys
import ta
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# Importar funções de indicadores
sys.path.append('.')
from RSI_MACD import *


# Configuração da página
st.set_page_config(
    page_title="Financial Agent Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Lista de stocks (apenas ações, sem criptomoedas)
STOCKS = ['AMZN', 'AAPL', 'GOOGL', 'MSFT', 'UDMY', 'NXE', 'SPY', 'CDR.WA', 'EH']

def load_stock_data(ticker):
    """Carrega dados de um stock específico"""
    try:
        # Tentar diferentes formatos de arquivo
        possible_names = [
            f"{ticker}.csv",
            f"{ticker.replace('.', '_')}.csv",
            f"{ticker.replace('-', '_')}.csv"
        ]
        
        for filename in possible_names:
            file_path = f"data/{filename}"
            if os.path.exists(file_path):
                # Ler CSV primeiro para verificar estrutura
                df_temp = pd.read_csv(file_path)
                
                # Verificar se 'Date' está na coluna 1 (índice 1)
                if 'Date' in df_temp.columns:
                    if df_temp.columns[1] == 'Date':
                        # Pular primeira linha, usar Date como índice
                        df = pd.read_csv(file_path, skiprows=1, index_col=1, parse_dates=True)
                    else:
                        # Formato antigo - Date como primeira coluna
                        df = pd.read_csv(file_path, skiprows=2, index_col='Date', parse_dates=True)
                else:
                    continue
                
                # Limpar e processar dados
                df = df.dropna()
                
                # Renomear colunas se necessário
                if len(df.columns) >= 4:
                    # Verificar ordem correta das colunas após pular 1 linha
                    # CSV: Price,Date,Close,High,Low,Open,Volume
                    # Após skiprows=1 e index_col=1: Close,High,Low,Open,Volume
                    expected_cols = ['Close', 'High', 'Low', 'Open']
                    if len(df.columns) >= 4:
                        # Manter nomes originais se estiverem corretos
                        if all(col in df.columns for col in expected_cols):
                            # Já está correto, não renomear
                            pass
                        else:
                            # Renomear para ordem esperada
                            df.columns = expected_cols + list(df.columns[len(expected_cols):])
                
                if len(df) > 0:
                    # Adicionar indicadores técnicos
                    df_with_indicators = add_indicators(df)
                    return df_with_indicators
        
        return None
    except Exception as e:
        st.error(f"Erro ao carregar dados de {ticker}: {str(e)}")
        return None

def calculate_moving_averages(df, periods=[20, 50]):
    """Calcula médias móveis"""
    df_copy = df.copy()
    for period in periods:
        df_copy[f'MA_{period}'] = df_copy['Close'].rolling(window=period).mean()
    return df_copy

def build_features(df):
    """Constrói features para o modelo ML (baseado no notebook)"""
    df = df.copy()
    
    # Converter Close para numérico
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna()
    
    # returns
    df["return"] = df["Close"].pct_change()
    
    # RSI
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    
    # MACD
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()
    df["MACD_HIST"] = macd.macd_diff()
    
    # volatilidade
    df["STD_14"] = df["Close"].rolling(14).std()
    
    # Bollinger
    ma20 = df["Close"].rolling(20).mean()
    std20 = df["Close"].rolling(20).std()
    df["BB_upper"] = ma20 + 2 * std20
    df["BB_lower"] = ma20 - 2 * std20
    
    # targets (ML)
    df["target_price"] = df["Close"].shift(-1)
    df["target_dir"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
    
    return df.dropna()

def train_ml_model(df):
    """Treina modelo ML como no notebook"""
    features = [
        "Open", "High", "Low", "Close",
        "RSI", "MACD", "MACD_SIGNAL", "MACD_HIST",
        "STD_14", "return"
    ]
    
    # Construir features
    df_features = build_features(df)
    
    if len(df_features) < 100:
        return None, None, None
    
    X = df_features[features]
    y_price = df_features["target_price"]
    
    # Time split (80/20)
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y_price.iloc[:split], y_price.iloc[split:]
    
    # Treinar modelo
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    
    # Calcular MAE
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    mae_percent = mae / y_test.mean() * 100
    
    return model, mae_percent, X_test

def predict_6_months(df):
    """Previsão usando modelo ML do notebook"""
    if len(df) < 100:
        return None, None, None
    
    # Treinar modelo
    model, mae_percent, X_test = train_ml_model(df)
    
    if model is None:
        return None, None, None
    
    # Prever próximo preço
    last_features = X_test.iloc[-1:].values
    predicted_price = model.predict(last_features)[0]
    
    # Projeção para 6 meses (usando tendência do modelo)
    current_price = df['Close'].iloc[-1]
    price_change_pct = ((predicted_price / current_price) - 1) * 100
    
    # Projetar para 6 meses (~126 dias úteis)
    # Assumindo taxa de crescimento diária consistente
    daily_change = (predicted_price / current_price) ** (1/126) - 1
    six_month_prediction = current_price * (1 + daily_change) ** 126
    
    # Calcular confiança baseada no MAE
    confidence = max(0, 100 - mae_percent)
    
    return six_month_prediction, price_change_pct, confidence

def create_price_chart(df):
    df_with_ma = calculate_moving_averages(df)
    
    fig = go.Figure()
    
    # Adicionar preço de fechamento
    fig.add_trace(go.Candlestick(
        x=df_with_ma.index,
        open=df_with_ma['Open'],
        high=df_with_ma['High'],
        low=df_with_ma['Low'],
        close=df_with_ma['Close'],
        name='Price',
        increasing_line_color='green',
        decreasing_line_color='red'
    ))
    
    # Adicionar médias móveis
    fig.add_trace(go.Scatter(
        x=df_with_ma.index,
        y=df_with_ma['MA_20'],
        mode='lines',
        name='MA 20',
        line=dict(color='blue', width=1)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_with_ma.index,
        y=df_with_ma['MA_50'],
        mode='lines',
        name='MA 50',
        line=dict(color='orange', width=1)
    ))
    
    fig.update_layout(
        title='Price Chart with Moving Averages',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        template='plotly_white',
        height=400
    )
    
    return fig


def main():
    # Header
    st.title("📊 Financial Agent Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("Stock Selection")
    selected_stock = st.sidebar.selectbox("Choose a stock:", STOCKS)
    
    # Carregar dados
    df = load_stock_data(selected_stock)
    
    if df is not None:
        # Métricas principais
        col1, col2, col3, col4, col5 = st.columns(5)
        
        current_price = df['Close'].iloc[-1]
        price_change = ((df['Close'].iloc[-1] / df['Close'].iloc[-30]) - 1) * 100 if len(df) > 30 else 0
        
        # Obter valores de indicadores
        current_rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 0
        current_macd = df['MACD'].iloc[-1] if 'MACD' in df.columns else 0
        
        with col1:
            st.metric("Current Price", f"${current_price:.2f}")
        
        with col2:
            st.metric("30-Day Change", f"{price_change:+.2f}%")
        
        with col3:
            rsi_signal = "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral"
            st.metric("RSI", f"{current_rsi:.1f}", rsi_signal)
        
        with col4:
            macd_signal = "Bullish" if current_macd > 0 else "Bearish"
            st.metric("MACD", f"{current_macd:.4f}", macd_signal)
        
        with col5:
            st.metric("Data Points", f"{len(df)}")
        
        st.markdown("---")
        
        # Gráfico de preços (apenas um, centralizado)
        price_fig = create_price_chart(df)
        st.plotly_chart(price_fig, use_container_width=True)
        
        # Previsão de 6 meses com ML
        st.markdown("---")
        st.subheader("🤖 6-Month Price Prediction (ML Model)")
        
        predicted_price, price_change_pct, confidence = predict_6_months(df)
        
        if predicted_price:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Predicted Price (6 months)", f"${predicted_price:.2f}")
            
            with col2:
                st.metric("Model Confidence", f"{confidence:.1f}%")
            
            st.info("🤖 **ML Model**: RandomForestRegressor trained on historical data with technical indicators (RSI, MACD, Bollinger Bands, Volatility)")
        else:
            st.warning("⚠️ Insufficient data for ML prediction (need at least 100 data points).")
    
    else:
        st.error(f"Could not load data for {selected_stock}. Please check if the CSV file exists in the data folder.")
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **EY AI Challenge 2026** | Financial Agent Dashboard")

if __name__ == "__main__":
    main()
