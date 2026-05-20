import pandas as pd
import ta
import numpy as np

def debug_indicators():
    """Diagnosticar problema com RSI e MACD"""
    
    print("🔍 DIAGNÓSTICO DOS INDICADORES")
    print("="*60)
    
    # Carregar dados do AAPL
    try:
        df = pd.read_csv('data/AAPL.csv', skiprows=1, index_col=1, parse_dates=True)
        df = df.dropna()
        
        # Renomear colunas
        df.columns = ['Close', 'High', 'Low', 'Open'] + list(df.columns[4:])
        
        print(f"✅ Dados carregados: {len(df)} registros")
        print(f"📅 Período: {df.index.min().date()} até {df.index.max().date()}")
        print()
        
        # Verificar tipos de dados
        print("📊 Tipos de dados:")
        print(df[['Close', 'High', 'Low', 'Open']].dtypes)
        print()
        
        # Verificar primeiros valores
        print("📈 Primeiros 5 dias - Preços:")
        print(df[['Close', 'High', 'Low', 'Open']].head())
        print()
        
        # Verificar se há valores não numéricos
        print("🔍 Verificação de valores não numéricos:")
        for col in ['Close', 'High', 'Low', 'Open']:
            non_numeric = df[col].apply(lambda x: not isinstance(x, (int, float, np.number))).sum()
            print(f"{col}: {non_numeric} valores não numéricos")
        print()
        
        # Calcular RSI
        print("📊 CÁLCULO DO RSI:")
        print("-" * 30)
        
        try:
            rsi = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
            
            print(f"RSI - Últimos 10 valores:")
            print(rsi.tail(10))
            print()
            print(f"RSI - Estatísticas:")
            print(f"  Mínimo: {rsi.min():.2f}")
            print(f"  Máximo: {rsi.max():.2f}")
            print(f"  Média: {rsi.mean():.2f}")
            print(f"  Atual: {rsi.iloc[-1]:.2f}")
            print()
            
            # Verificar valores anormais
            rsi_over_90 = (rsi > 90).sum()
            rsi_under_10 = (rsi < 10).sum()
            print(f"RSI > 90: {rsi_over_90} dias")
            print(f"RSI < 10: {rsi_under_10} dias")
            print()
            
        except Exception as e:
            print(f"❌ Erro ao calcular RSI: {e}")
            print()
        
        # Calcular MACD
        print("📈 CÁLCULO DO MACD:")
        print("-" * 30)
        
        try:
            macd = ta.trend.MACD(close=df['Close'], window_slow=26, window_fast=12, window_sign=9)
            
            macd_line = macd.macd()
            macd_signal = macd.macd_signal()
            macd_hist = macd.macd_diff()
            
            print("MACD Line - Últimos 10 valores:")
            print(macd_line.tail(10))
            print()
            print("MACD - Estatísticas:")
            print(f"  Mínimo: {macd_line.min():.4f}")
            print(f"  Máximo: {macd_line.max():.4f}")
            print(f"  Média: {macd_line.mean():.4f}")
            print(f"  Atual: {macd_line.iloc[-1]:.4f}")
            print()
            
            # Verificar valores anormais
            macd_large = (abs(macd_line) > 10).sum()
            print(f"MACD com |valor| > 10: {macd_large} dias")
            print()
            
        except Exception as e:
            print(f"❌ Erro ao calcular MACD: {e}")
            print()
        
        # Testar cálculo manual de RSI para alguns dias
        print("🔧 TESTE MANUAL - RSI:")
        print("-" * 30)
        
        # Pegar últimos 20 dias para cálculo manual
        recent_prices = df['Close'].tail(20)
        
        # Calcular mudanças
        delta = recent_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Calcular RS e RSI
        rs = gain / loss
        rsi_manual = 100 - (100 / (1 + rs))
        
        print("RSI Manual - Últimos 6 valores:")
        print(rsi_manual.tail(6))
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        return False

if __name__ == "__main__":
    debug_indicators()
