import yfinance as yf
import pandas as pd
import os

ASSETS = [
    "AMZN", "AAPL", "GOOGL", "MSFT", "UDMY", "NXE", "SPY", "CDR.WA", "EH",
    "BTC-USD", "ETH-USD"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def download_data(period="1y", interval="1d"):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    for asset in ASSETS:
        print(f"Downloading data for {asset}...")
        ticker = yf.Ticker(asset)
        df = ticker.history(period=period, interval=interval)
        if not df.empty:
            df.to_csv(os.path.join(DATA_DIR, f"{asset}.csv"))
            print(f"Saved {asset}.csv")
        else:
            print(f"No data found for {asset}")

if __name__ == "__main__":
    download_data()
