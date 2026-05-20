from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, auth, database, data_router, updater, crud
from .routers import users, portfolio, recommendations
import asyncio

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Financial Decision Support API")

@app.on_event("startup")
async def startup_event():
    # In a real app, you might want to run the updater in a separate process
    # or have a more robust scheduling system (e.g., Celery, APScheduler).
    # For a hackathon, this is a simple and effective approach.
    asyncio.create_task(updater.update_financial_data())

# --- Routers ---
app.include_router(data_router.router)
app.include_router(users.router)
app.include_router(portfolio.router)
app.include_router(recommendations.router)


# --- Authentication Endpoints ---
@app.post("/api/auth/register", response_model=schemas.Token, tags=["Authentication"])
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = auth.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_pwd = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_pwd)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    token = auth.create_access_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=schemas.Token, tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.get_user(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Public Endpoints ---
@app.get("/api/tickers", response_model=List[schemas.Ticker], tags=["Data"])
def read_tickers(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    """
    Retrieve a list of all available tickers.
    """
    tickers = crud.get_tickers(db, skip=skip, limit=limit)
    return tickers

