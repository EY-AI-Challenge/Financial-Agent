from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models, crud, database

router = APIRouter(
    prefix="/api/recommendations",
    tags=["Recommendations"],
)

@router.get("/", response_model=List[schemas.InvestmentRecommendation])
def read_recommendations(db: Session = Depends(database.get_db)):
    """
    Retrieve all PENDING investment recommendations.
    """
    return crud.get_recommendations(db)

@router.post("/{recommendation_id}/accept", response_model=schemas.Portfolio)
def accept_recommendation(recommendation_id: int, db: Session = Depends(database.get_db)):
    """
    Accept an investment recommendation.
    This updates the recommendation status and creates a new portfolio transaction.
    """
    rec = crud.get_recommendation_by_id(db, recommendation_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    if rec.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recommendation already actioned")

    crud.update_recommendation_status(db, recommendation_id, "ACCEPTED")
    
    # This is a simplified logic. A real app would get the live price.
    # Here we assume the transaction happens at the predicted price.
    transaction = schemas.PortfolioCreate(
        ticker_symbol=rec.prediction.ticker_symbol,
        transaction_type="BUY", # Assuming recommendations are 'BUY'
        quantity=1, # Simplified: assume buying 1 unit
        price_per_unit=rec.prediction.predicted_price,
        recommendation_id=recommendation_id
    )
    return crud.create_portfolio_transaction(db, transaction)
