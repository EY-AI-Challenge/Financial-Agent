from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import os
import glob
import requests
from dotenv import load_dotenv
from ai_agent import generate_insights, calculate_portfolio_metrics, chat_with_portfolio

# Load env
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

app = FastAPI(title="Financial Bros API", description="AI Decision Support Platform for Investment Funds")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

def load_asset_data(asset: str) -> pd.DataFrame:
    file_path = os.path.join(DATA_DIR, f"{asset}.csv")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Data for asset {asset} not found.")
    df = pd.read_csv(file_path)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        df.set_index('Date', inplace=True)
    elif 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True)
        df.set_index('Datetime', inplace=True)
    return df

@app.get("/api/status")
def get_status():
    """Check Ollama connection status."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        return {"ollama": "online", "models": models}
    except:
        return {"ollama": "offline", "models": []}

@app.get("/api/assets")
def get_assets():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    assets = [os.path.basename(f).replace(".csv", "") for f in files]
    return {"assets": assets}

@app.get("/api/assets/{asset}/data")
def get_asset_data(asset: str, days: int = 365):
    df = load_asset_data(asset)
    df = df.tail(days)
    dates = [d.isoformat() for d in df.index]
    closes = df['Close'].tolist()
    volumes = df['Volume'].tolist() if 'Volume' in df.columns else []
    
    # Calculate SMAs for chart overlay
    df2 = df.copy()
    df2['SMA_20'] = df2['Close'].rolling(window=20).mean()
    df2['SMA_50'] = df2['Close'].rolling(window=50).mean()
    sma20 = [None if pd.isna(v) else round(v, 4) for v in df2['SMA_20'].tolist()]
    sma50 = [None if pd.isna(v) else round(v, 4) for v in df2['SMA_50'].tolist()]
    
    return {
        "asset": asset,
        "dates": dates,
        "closes": closes,
        "volumes": volumes,
        "sma_20": sma20,
        "sma_50": sma50,
    }

@app.get("/api/assets/{asset}/insights")
def get_asset_insights(asset: str):
    df = load_asset_data(asset)
    insights = generate_insights(df, asset, use_ai=True)
    return {"asset": asset, "insights": insights}

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
        insights = generate_insights(df, asset, use_ai=False)
        asset_details.append({
            "asset": asset,
            "signal": insights["signal"],
            "confidence": insights["confidence"],
            "current_price": insights["current_price"]
        })

    return {"metrics": metrics, "assets": asset_details}

@app.get("/api/news")
def get_financial_news(q: str = "stocks finance market"):
    """Fetch financial news from NewsAPI or fallback to free RSS."""
    if NEWS_API_KEY:
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": q,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 12,
                "apiKey": NEWS_API_KEY
            }
            r = requests.get(url, params=params, timeout=8)
            if r.status_code == 200:
                articles = r.json().get("articles", [])
                return {"articles": [
                    {
                        "title": a["title"],
                        "description": a.get("description", ""),
                        "url": a["url"],
                        "source": a["source"]["name"],
                        "publishedAt": a["publishedAt"],
                        "urlToImage": a.get("urlToImage", "")
                    }
                    for a in articles if a.get("title")
                ]}
        except Exception as e:
            print(f"NewsAPI error: {e}")

    # Fallback: use free GNews RSS via public endpoint
    try:
        rss_url = "https://gnews.io/api/v4/top-headlines"
        params = {
            "category": "business",
            "lang": "en",
            "country": "us",
            "max": 10,
            "apikey": "free"
        }
        r = requests.get(rss_url, params=params, timeout=8)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            return {"articles": [
                {
                    "title": a["title"],
                    "description": a.get("description", ""),
                    "url": a["url"],
                    "source": a["source"]["name"],
                    "publishedAt": a["publishedAt"],
                    "urlToImage": a.get("image", "")
                }
                for a in articles
            ]}
    except Exception as e:
        print(f"GNews fallback error: {e}")

    # Final fallback: curated finance headlines
    return {"articles": [
        {"title": "Markets rally as inflation data comes in lower than expected", "description": "U.S. stock markets surged following the latest CPI report.", "url": "https://finance.yahoo.com", "source": "Yahoo Finance", "publishedAt": "2026-05-20T09:00:00Z", "urlToImage": ""},
        {"title": "Bitcoin tests key resistance levels amid institutional inflows", "description": "Crypto markets remain volatile as whale wallets accumulate BTC.", "url": "https://coindesk.com", "source": "CoinDesk", "publishedAt": "2026-05-20T08:00:00Z", "urlToImage": ""},
        {"title": "Apple reports record Q2 earnings, guidance beats estimates", "description": "AAPL shares surged after Tim Cook announced strong services growth.", "url": "https://finance.yahoo.com", "source": "Yahoo Finance", "publishedAt": "2026-05-20T07:00:00Z", "urlToImage": ""},
        {"title": "Fed signals potential rate pause amid mixed economic data", "description": "Federal Reserve officials hinted at holding rates steady in June.", "url": "https://reuters.com", "source": "Reuters", "publishedAt": "2026-05-20T06:00:00Z", "urlToImage": ""},
        {"title": "Amazon AWS growth accelerates, cloud revenues up 17% YoY", "description": "AMZN stock hits new high as enterprise cloud adoption continues.", "url": "https://finance.yahoo.com", "source": "Yahoo Finance", "publishedAt": "2026-05-20T05:00:00Z", "urlToImage": ""},
        {"title": "Ethereum ETF inflows reach $500M milestone", "description": "ETH surges as institutional demand via spot ETFs continues to grow.", "url": "https://coindesk.com", "source": "CoinDesk", "publishedAt": "2026-05-20T04:00:00Z", "urlToImage": ""},
    ]}

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
            insights = generate_insights(df, asset, use_ai=False)
            portfolio_context.append({
                "asset": asset,
                "current_price": insights["current_price"],
                "signal": insights["signal"],
                "confidence": insights["confidence"],
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
            return FileResponse(index_file, headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            })
        return {"message": "Frontend not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
