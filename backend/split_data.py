import os
import pandas as pd
from pathlib import Path

DATA_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data"
TRAIN_DIR = DATA_DIR / "train"
TEST_DIR = DATA_DIR / "test"

TRAIN_START = pd.Timestamp("2025-05-20")
TRAIN_END = pd.Timestamp("2026-03-15")
TEST_START = pd.Timestamp("2026-03-16")
TEST_END = pd.Timestamp("2026-05-19")


def split_asset_file(csv_path: Path) -> None:
    df = pd.read_csv(csv_path)
    if "Date" not in df.columns and "Datetime" in df.columns:
        df = df.rename(columns={"Datetime": "Date"})

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc=True).dt.tz_convert(None)
    df = df.dropna(subset=["Date"]).sort_values("Date")

    train_df = df[(df["Date"] >= TRAIN_START) & (df["Date"] < TRAIN_END)]
    test_df = df[(df["Date"] >= TEST_START) & (df["Date"] <= TEST_END)]

    asset_name = csv_path.name
    train_out = TRAIN_DIR / asset_name
    test_out = TEST_DIR / asset_name

    train_df.to_csv(train_out, index=False)
    test_df.to_csv(test_out, index=False)

    print(f"Saved train: {train_out} ({len(train_df)} rows), test: {test_out} ({len(test_df)} rows)")


def main() -> None:
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(DATA_DIR.glob("*.csv"))
    for csv_path in csv_files:
        if csv_path.name in {"train", "test"}:
            continue
        split_asset_file(csv_path)


if __name__ == "__main__":
    main()
