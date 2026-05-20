from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import os
import glob
from ai_agent import generate_insights, calculate_portfolio_metrics, chat_with_portfolio

app = FastAPI(title="Financial Bros API", description="AI Decision Support Platform for Investment Funds")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/train")
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

def load_asset_data(asset: str) -> pd.DataFrame:
    file_path = os.path.join(DATA_DIR, f"{asset}.csv")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Data for asset {asset} not found.")
    
    # Try to parse Date or Datetime column
    df = pd.read_csv(file_path)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        df.set_index('Date', inplace=True)
    elif 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True)
        df.set_index('Datetime', inplace=True)
    return df

@app.get("/api/assets")
def get_assets():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    assets = [os.path.basename(f).replace(".csv", "") for f in files]
    return {"assets": assets}

@app.get("/api/assets/{asset}/data")
def get_asset_data(asset: str, days: int = 365):
    df = load_asset_data(asset)
    df = df.tail(days)
    
    # Format for frontend chart
    dates = [d.isoformat() for d in df.index]
    closes = df['Close'].tolist()
    volumes = df['Volume'].tolist() if 'Volume' in df.columns else []
    
    return {
        "asset": asset,
        "dates": dates,
        "closes": closes,
        "volumes": volumes
    }

@app.get("/api/assets/{asset}/insights")
def get_asset_insights(asset: str):
    df = load_asset_data(asset)
    insights = generate_insights(df, asset)
    return {
        "asset": asset,
        "insights": insights
    }

@app.get("/api/portfolio/summary")
def get_portfolio_summary():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    assets = [os.path.basename(f).replace(".csv", "") for f in files]
    
    asset_data_dict = {}
    for asset in assets:
        try:
            df = load_asset_data(asset)
            asset_data_dict[asset] = df
        except:
            continue
            
    metrics = calculate_portfolio_metrics(asset_data_dict)
    
    asset_details = []
    for asset, df in asset_data_dict.items():
        insights = generate_insights(df, asset)
        asset_details.append({
            "asset": asset,
            "signal": insights["signal"],
            "confidence": insights["confidence"],
            "current_price": insights["current_price"]
        })
        
    return {
        "metrics": metrics,
        "assets": asset_details
    }

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    assets = [os.path.basename(f).replace(".csv", "") for f in files]

    portfolio_context = []
    for asset in assets:
        try:
            df = load_asset_data(asset)
            insights = generate_insights(df, asset)
            portfolio_context.append({
                "asset": asset,
                "current_price": insights["current_price"],
                "signal": insights["signal"],
                "confidence": insights["confidence"],
                "sma_20": insights.get("sma_20"),
                "sma_50": insights.get("sma_50"),
            })
        except:
            continue

    response = chat_with_portfolio(request.message, portfolio_context)
    return {"response": response}


# Mount frontend
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
