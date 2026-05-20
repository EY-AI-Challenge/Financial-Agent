from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models, crud, database

router = APIRouter(
    prefix="/api/portfolio",
    tags=["Portfolio"],
)

@router.get("/", response_model=List[schemas.Portfolio])
def read_portfolio(db: Session = Depends(database.get_db)):
    """
    Retrieve all portfolio transactions.
    """
    return crud.get_portfolio(db)

@router.post("/", response_model=schemas.Portfolio)
def add_portfolio_transaction(transaction: schemas.PortfolioCreate, db: Session = Depends(database.get_db)):
    """
    Add a new 'BUY' or 'SELL' transaction to the portfolio.
    """
    return crud.create_portfolio_transaction(db=db, transaction=transaction)
