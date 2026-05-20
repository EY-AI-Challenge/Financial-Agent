"""
main.py — Command-line interface for the Stock Price Predictor.

Basic usage
-----------
  # Single ticker from CSV
  python main.py --csv AAPL.csv --ticker AAPL

  # Multiple CSVs (one per ticker)
  python main.py --csv AAPL.csv MSFT.csv BTC.csv --ticker AAPL MSFT BTC

  # Disable Chronos (no HuggingFace access needed)
  python main.py --csv AAPL.csv --ticker AAPL --no-chronos

  # Larger Chronos model for better accuracy
  python main.py --csv AAPL.csv --ticker AAPL --chronos-size base

  # Save plots to a directory
  python main.py --csv AAPL.csv --ticker AAPL --out-dir results/

  # Verbose output
  python main.py --csv AAPL.csv --ticker AAPL --verbose

Output
------
  - Console summary table with price predictions + confidence intervals
  - PNG forecast charts (if --out-dir provided)
  - JSON results file (if --out-dir provided)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Make sure local modules are importable when running from project root
sys.path.insert(0, str(Path(__file__).parent))

from predictor import StockPredictor


# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stock/Crypto Price Predictor — LightGBM + Prophet + Chronos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--csv", nargs="+", required=True,
        help="Path(s) to OHLCV CSV file(s). One per ticker.",
    )
    p.add_argument(
        "--ticker", nargs="+",
        help="Ticker symbol(s) corresponding to each CSV. "
             "Defaults to CSV filename stem.",
    )
    p.add_argument(
        "--no-chronos", action="store_true",
        help="Skip Chronos (no internet / HuggingFace access needed).",
    )
    p.add_argument(
        "--chronos-size",
        choices=["tiny", "mini", "small", "base", "large"],
        default="small",
        help="Chronos model size (default: small ≈ 46M params).",
    )
    p.add_argument(
        "--prophet-years", type=int, default=5,
        help="Years of history to give Prophet (default: 5).",
    )
    p.add_argument(
        "--cv-splits", type=int, default=5,
        help="Time-series CV folds for LightGBM evaluation (default: 5).",
    )
    p.add_argument(
        "--out-dir", type=str, default=None,
        help="Directory to save plots and JSON results.",
    )
    p.add_argument(
        "--history-days", type=int, default=500,
        help="Days of history shown in the chart (default: 500).",
    )
    p.add_argument(
        "--verbose", action="store_true",
        help="Print detailed training logs.",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------

def run_one(
    csv_path: str,
    ticker: str,
    use_chronos: bool,
    chronos_size: str,
    prophet_years: int,
    cv_splits: int,
    out_dir: Path | None,
    history_days: int,
    verbose: bool,
) -> dict:
    sp = StockPredictor(
        ticker=ticker,
        use_chronos=use_chronos,
        chronos_size=chronos_size,
        prophet_years=prophet_years,
        n_cv_splits=cv_splits,
    )
    sp.load_data(csv_path)
    sp.train(verbose=verbose)
    results = sp.predict()
    StockPredictor.print_summary(results, ticker)

    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        plot_path = out_dir / f"{ticker}_forecast.png"
        sp.plot(results, save_path=plot_path, history_days=history_days)

        # Serialise results to JSON
        json_path = out_dir / f"{ticker}_results.json"
        serialisable = {}
        for h, d in results.items():
            if d is None:
                serialisable[h] = None
                continue
            serialisable[h] = {
                k: (float(v) if isinstance(v, (float, np.floating)) else v)
                for k, v in d.items()
                if k != "sources"
            }
            if d.get("sources"):
                serialisable[h]["sources"] = {
                    m: {kk: float(vv) for kk, vv in sv.items()}
                    for m, sv in d["sources"].items()
                }
        with open(json_path, "w") as f:
            json.dump({"ticker": ticker, "predictions": serialisable}, f, indent=2)
        print(f"  JSON saved  → {json_path}")

    return results


# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    csv_paths = args.csv
    tickers = args.ticker or [Path(p).stem for p in csv_paths]

    if len(csv_paths) != len(tickers):
        print(
            f"ERROR: --csv ({len(csv_paths)} files) and "
            f"--ticker ({len(tickers)} names) counts must match."
        )
        sys.exit(1)

    out_dir = Path(args.out_dir) if args.out_dir else None

    all_results = {}
    for csv, ticker in zip(csv_paths, tickers):
        all_results[ticker] = run_one(
            csv_path=csv,
            ticker=ticker,
            use_chronos=not args.no_chronos,
            chronos_size=args.chronos_size,
            prophet_years=args.prophet_years,
            cv_splits=args.cv_splits,
            out_dir=out_dir,
            history_days=args.history_days,
            verbose=args.verbose,
        )

    print("\n✓ All done.")


if __name__ == "__main__":
    main()
