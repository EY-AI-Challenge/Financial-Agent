import yfinance as yf
import pandas as pd
import os

stocks = ["AMZN", "AAPL", "GOOGL", "MSFT", "UDMY", "NXE", "SPY", "CDR.WA", "EH"]
cryptos = ["BTC-USD", "ETH-USD"]
all_tickers = stocks + cryptos

output_dir = "financial_data"
os.makedirs(output_dir, exist_ok=True)

print("Starting download process...")

for ticker in all_tickers:
    print(f"Fetching data for {ticker}...")
    data = yf.download(ticker, period="max", progress=False)
    
    if not data.empty:
        # --- THE FIX ---
        # Check if the columns have multiple header rows
        if isinstance(data.columns, pd.MultiIndex):
            # Keep only the top header row (Close, High, Low, etc.) and drop the Ticker row
            data.columns = data.columns.get_level_values(0)
        # ---------------
        
        file_path = os.path.join(output_dir, f"{ticker}.csv")
        data.to_csv(file_path)
        print(f" -> Saved to {file_path}")
    else:
        print(f" -> Warning: No data found for {ticker}")

print("\nAll downloads complete!")