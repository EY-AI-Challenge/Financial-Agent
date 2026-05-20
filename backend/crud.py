from sqlalchemy.orm import Session
import models, schemas

# --- Portfolio CRUD ---
def get_portfolio(db: Session):
    return db.query(models.Portfolio).all()

def create_portfolio_transaction(db: Session, transaction: schemas.PortfolioCreate):
    db_transaction = models.Portfolio(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# --- Ticker CRUD ---
def get_tickers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Ticker).offset(skip).limit(limit).all()

# --- Recommendations CRUD ---
def get_recommendations(db: Session, status: str = "PENDING"):
    return db.query(models.InvestmentRecommendation).filter(
        models.InvestmentRecommendation.status == status
    ).all()

def get_recommendation_by_id(db: Session, recommendation_id: int):
    return db.query(models.InvestmentRecommendation).filter(models.InvestmentRecommendation.id == recommendation_id).first()

def update_recommendation_status(db: Session, recommendation_id: int, new_status: str):
    db_rec = get_recommendation_by_id(db, recommendation_id)
    if db_rec:
        db_rec.status = new_status
        db.commit()
        db.refresh(db_rec)
    return db_rec
