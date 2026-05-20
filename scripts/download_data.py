from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf


ASSETS = [
    "AMZN",
    "AAPL",
    "GOOGL",
    "MSFT",
    "UDMY",
    "NXE",
    "SPY",
    "CDR.WA",
    "EH",
    "BTC-USD",
    "ETH-USD",
]

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"

DOWNLOAD_PLAN = {
    "daily": {"period": "5y", "interval": "1d", "folder": RAW_DIR / "daily"},
    "hourly": {"period": "60d", "interval": "1h", "folder": RAW_DIR / "hourly"},
}


def download_asset(symbol: str, period: str, interval: str) -> pd.DataFrame:
    frame = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if frame.empty:
        raise ValueError(f"No data returned for {symbol} with {period=} and {interval=}")

    frame = frame.reset_index()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [col[0] if col[1] == "" else col[0] for col in frame.columns]

    time_col = "Datetime" if "Datetime" in frame.columns else "Date"
    frame[time_col] = pd.to_datetime(frame[time_col])
    frame["Ticker"] = symbol
    return frame


def main() -> None:
    for dataset_name, config in DOWNLOAD_PLAN.items():
        folder = config["folder"]
        folder.mkdir(parents=True, exist_ok=True)

        print(f"\nDownloading {dataset_name} data...")
        for symbol in ASSETS:
            print(f"  - {symbol}")
            frame = download_asset(symbol, config["period"], config["interval"])
            output_path = folder / f"{symbol}.csv"
            frame.to_csv(output_path, index=False)

        print(f"Saved {dataset_name} CSVs to {folder}")


if __name__ == "__main__":
    main()
