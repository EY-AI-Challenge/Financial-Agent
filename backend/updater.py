import asyncio
import yfinance as yf
import os
import pandas as pd
from datetime import datetime

TICKERS = ["AMZN", "AAPL", "GOOGL", "MSFT", "UDMY", "NXE", "SPY", "CDR.WA", "EH", "BTC-USD", "ETH-USD"]
DATA_DIR = "financial_data"

async def update_financial_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    while True:
        print(f"[{datetime.now()}] Starting daily data update...")
        for ticker in TICKERS:
            try:
                data = yf.download(ticker, period="1y", interval="1d")
                if not data.empty:
                    data.to_csv(os.path.join(DATA_DIR, f"{ticker}.csv"))
                    print(f"Updated {ticker}")
            except Exception as e:
                print(f"Error updating {ticker}: {e}")
        
        # Sleep for 24 hours
        await asyncio.sleep(86400)
