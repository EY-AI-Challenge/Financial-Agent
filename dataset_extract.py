import yfinance as yf
import os

# 1. Define the tickers extracted from the image
stocks = ["AMZN", "AAPL", "GOOGL", "MSFT", "UDMY", "NXE", "SPY", "CDR.WA", "EH"]
cryptos = ["BTC-USD", "ETH-USD"]

# Combine into a single list
all_tickers = stocks + cryptos

# 2. Create a directory to store the CSV files
output_dir = "financial_data"
os.makedirs(output_dir, exist_ok=True)

# 3. Download and save data for each ticker
print("Starting download process...")

for ticker in all_tickers:
    print(f"Fetching data for {ticker}...")
    
    # Download historical data. 
    # You can change period="max" to "1y", "5y", etc., depending on your needs.
    data = yf.download(ticker, period="max", progress=False)
    
    # Check if data was successfully retrieved
    if not data.empty:
        # Save to CSV
        file_path = os.path.join(output_dir, f"{ticker}.csv")
        data.to_csv(file_path)
        print(f" -> Saved to {file_path}")
    else:
        print(f" -> Warning: No data found for {ticker}")

print("\nAll downloads complete!")