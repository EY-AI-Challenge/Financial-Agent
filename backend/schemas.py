from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional
from decimal import Decimal

# --- Ticker Schemas ---
class TickerBase(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: Optional[str] = None

class TickerCreate(TickerBase):
    pass

class Ticker(TickerBase):
    last_updated: Optional[datetime] = None
    class Config:
        from_attributes = True

# --- HistoricalPriceData Schemas ---
class HistoricalPriceDataBase(BaseModel):
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

class HistoricalPriceData(HistoricalPriceDataBase):
    ticker_symbol: str
    class Config:
        from_attributes = True

# --- AIPrediction Schemas ---
class AIPredictionBase(BaseModel):
    ticker_symbol: str
    target_date: date
    horizon: str
    predicted_price: Decimal
    confidence: Optional[float] = None

class AIPrediction(AIPredictionBase):
    id: int
    generated_at: datetime
    class Config:
        from_attributes = True

# --- InvestmentRecommendation Schemas ---
class InvestmentRecommendationBase(BaseModel):
    prediction_id: int
    type: str
    justification: Optional[str] = None
    status: str

class InvestmentRecommendation(InvestmentRecommendationBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Portfolio Schemas ---
class PortfolioBase(BaseModel):
    ticker_symbol: str
    transaction_type: str
    quantity: Decimal
    price_per_unit: Decimal

class PortfolioCreate(PortfolioBase):
    recommendation_id: Optional[int] = None

class Portfolio(PortfolioBase):
    id: int
    transaction_date: datetime
    recommendation_id: Optional[int] = None
    class Config:
        from_attributes = True
