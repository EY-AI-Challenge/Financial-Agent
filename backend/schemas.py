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
        orm_mode = True

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
        orm_mode = True

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
        orm_mode = True

# --- InvestmentRecommendation Schemas ---
class InvestmentRecommendationBase(BaseModel):
    prediction_id: int
    type: str
    justification: Optional[str] = None
    status: str

class InvestmentRecommendation(InvestmentRecommendationBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        orm_mode = True

# --- UserPortfolio Schemas ---
class UserPortfolioBase(BaseModel):
    ticker_symbol: str
    transaction_type: str
    quantity: Decimal
    price_per_unit: Decimal

class UserPortfolioCreate(UserPortfolioBase):
    recommendation_id: Optional[int] = None

class UserPortfolio(UserPortfolioBase):
    id: int
    user_id: int
    transaction_date: datetime
    recommendation_id: Optional[int] = None
    class Config:
        orm_mode = True

# --- User Schemas ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    risk_profile: Optional[str] = None
    recommendations: List[InvestmentRecommendation] = []
    portfolio: List[UserPortfolio] = []
    class Config:
        orm_mode = True

# --- Token Schema ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
