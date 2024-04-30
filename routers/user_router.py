from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from typing import List
import models
import schemas
from sqlalchemy.orm import Session


user_router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@user_router.get('/', response_model=List[schemas.UserBase])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()

    return users
