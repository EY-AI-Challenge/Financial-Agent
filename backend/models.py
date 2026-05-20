from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, Float, BigInteger, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    risk_profile = Column(String)

    recommendations = relationship("InvestmentRecommendation", back_populates="user")
    portfolio = relationship("UserPortfolio", back_populates="user")

class Ticker(Base):
    __tablename__ = "tickers"
    symbol = Column(String, primary_key=True, index=True)
    name = Column(String)
    market = Column(String)
    last_updated = Column(DateTime)

    historical_data = relationship("HistoricalPriceData", back_populates="ticker")
    predictions = relationship("AIPrediction", back_populates="ticker")

class HistoricalPriceData(Base):
    __tablename__ = "historical_price_data"
    ticker_symbol = Column(String, ForeignKey("tickers.symbol"), primary_key=True)
    date = Column(Date, primary_key=True)
    open = Column(Numeric(10, 2))
    high = Column(Numeric(10, 2))
    low = Column(Numeric(10, 2))
    close = Column(Numeric(10, 2))
    volume = Column(BigInteger)

    ticker = relationship("Ticker", back_populates="historical_data")

class AIPrediction(Base):
    __tablename__ = "ai_predictions"
    id = Column(Integer, primary_key=True, index=True)
    ticker_symbol = Column(String, ForeignKey("tickers.symbol"))
    generated_at = Column(DateTime, default=datetime.utcnow)
    target_date = Column(Date)
    horizon = Column(String) # e.g., "1w", "1m", "1y"
    predicted_price = Column(Numeric(10, 2))
    confidence = Column(Float)

    ticker = relationship("Ticker", back_populates="predictions")
    recommendations = relationship("InvestmentRecommendation", back_populates="prediction")

class InvestmentRecommendation(Base):
    __tablename__ = "investment_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    prediction_id = Column(Integer, ForeignKey("ai_predictions.id"))
    type = Column(String) # e.g., "BUY", "SELL", "HOLD"
    justification = Column(Text)
    status = Column(String, default="PENDING") # e.g., "PENDING", "ACCEPTED", "REJECTED"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recommendations")
    prediction = relationship("AIPrediction", back_populates="recommendations")
    transactions = relationship("UserPortfolio", back_populates="recommendation")

class UserPortfolio(Base):
    __tablename__ = "user_portfolio"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker_symbol = Column(String, ForeignKey("tickers.symbol"))
    transaction_type = Column(String) # e.g., "BUY", "SELL"
    quantity = Column(Numeric(12, 6))
    price_per_unit = Column(Numeric(10, 2))
    transaction_date = Column(DateTime, default=datetime.utcnow)
    recommendation_id = Column(Integer, ForeignKey("investment_recommendations.id"), nullable=True)

    user = relationship("User", back_populates="portfolio")
    ticker = relationship("Ticker")
    recommendation = relationship("InvestmentRecommendation", back_populates="transactions")
