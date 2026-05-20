from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database, data_router, updater, crud
from .routers import portfolio, recommendations
import asyncio

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Financial Decision Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:80",
        "http://127.0.0.1:80",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # In a real app, you might want to run the updater in a separate process
    # or have a more robust scheduling system (e.g., Celery, APScheduler).
    # For a hackathon, this is a simple and effective approach.
    asyncio.create_task(updater.update_financial_data())

# --- Routers ---
app.include_router(data_router.router)
app.include_router(portfolio.router)
app.include_router(recommendations.router)


# --- Public Endpoints ---
@app.get("/api/tickers", response_model=List[schemas.Ticker], tags=["Data"])
def read_tickers(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    """
    Retrieve a list of all available tickers.
    """
    tickers = crud.get_tickers(db, skip=skip, limit=limit)
    return tickers

