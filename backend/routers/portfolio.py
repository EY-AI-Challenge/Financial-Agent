from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models, auth, crud, database

router = APIRouter(
    prefix="/api/portfolio",
    tags=["Portfolio"],
    dependencies=[Depends(auth.get_current_user)],
)

@router.get("/", response_model=List[schemas.UserPortfolio])
def read_user_portfolio(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """
    Retrieve all portfolio transactions for the current user.
    """
    return crud.get_portfolio_by_user(db, user_id=current_user.id)

@router.post("/", response_model=schemas.UserPortfolio)
def add_portfolio_transaction(transaction: schemas.UserPortfolioCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """
    Add a new 'BUY' or 'SELL' transaction to the current user's portfolio.
    """
    return crud.create_portfolio_transaction(db=db, transaction=transaction, user_id=current_user.id)
