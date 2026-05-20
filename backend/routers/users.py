from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models, auth, crud, database

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    Get the profile for the current authenticated user.
    """
    return current_user
