from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models, auth, crud, database

router = APIRouter(
    prefix="/api/recommendations",
    tags=["Recommendations"],
    dependencies=[Depends(auth.get_current_user)],
)

@router.get("/", response_model=List[schemas.InvestmentRecommendation])
def read_user_recommendations(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """
    Retrieve all PENDING investment recommendations for the current user.
    """
    return crud.get_recommendations_by_user(db, user_id=current_user.id)

@router.post("/{recommendation_id}/accept", response_model=schemas.UserPortfolio)
def accept_recommendation(recommendation_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """
    Accept an investment recommendation.
    This updates the recommendation status and creates a new portfolio transaction.
    """
    rec = crud.get_recommendation_by_id(db, recommendation_id)
    if not rec or rec.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    if rec.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recommendation already actioned")

    crud.update_recommendation_status(db, recommendation_id, "ACCEPTED")
    
    # This is a simplified logic. A real app would get the live price.
    # Here we assume the transaction happens at the predicted price.
    transaction = schemas.UserPortfolioCreate(
        ticker_symbol=rec.prediction.ticker_symbol,
        transaction_type="BUY", # Assuming recommendations are 'BUY'
        quantity=1, # Simplified: assume buying 1 unit
        price_per_unit=rec.prediction.predicted_price,
        recommendation_id=recommendation_id
    )
    return crud.create_portfolio_transaction(db, transaction, user_id=current_user.id)
