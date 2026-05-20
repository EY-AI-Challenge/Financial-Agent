from sqlalchemy.orm import Session
import models, schemas

# --- User Portfolio CRUD ---
def get_portfolio_by_user(db: Session, user_id: int):
    return db.query(models.UserPortfolio).filter(models.UserPortfolio.user_id == user_id).all()

def create_portfolio_transaction(db: Session, transaction: schemas.UserPortfolioCreate, user_id: int):
    db_transaction = models.UserPortfolio(**transaction.dict(), user_id=user_id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# --- Ticker CRUD ---
def get_tickers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Ticker).offset(skip).limit(limit).all()

# --- Recommendations CRUD ---
def get_recommendations_by_user(db: Session, user_id: int, status: str = "PENDING"):
    return db.query(models.InvestmentRecommendation).filter(
        models.InvestmentRecommendation.user_id == user_id,
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
