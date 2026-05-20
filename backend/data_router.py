from fastapi import APIRouter, HTTPException
import pandas as pd
import os

router = APIRouter()
DATA_DIR = "financial_data"

@router.get("/api/data/history/{ticker}")
def get_ticker_history(ticker: str):
    file_path = os.path.join(DATA_DIR, f"{ticker}.csv")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Ticker data not found")
    
    df = pd.read_csv(file_path)
    return df.to_dict(orient="records")
