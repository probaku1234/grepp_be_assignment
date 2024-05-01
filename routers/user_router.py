import hashlib

from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from typing import List
import models
import schemas
from sqlalchemy.orm import Session
from starlette import status

from util import encode_jwt

user_router = APIRouter(
    prefix='/users',
    tags=['Users']
)


def _encrypt_password(password):
    # Create an MD5 hash object
    md5 = hashlib.md5()

    # Update the hash object with the password
    md5.update(password.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    encrypted_password = md5.hexdigest()

    return encrypted_password


@user_router.get('/', response_model=List[schemas.UserBase])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()

    return users


@user_router.post('/login')
def login(login_user: schemas.LoginUser, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.user_id == login_user.user_id and models.User.password == _encrypt_password(
            login_user.password)).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The id or password is not right")

    # create jwt token and return
    return {'token': encode_jwt(user.user_id, user.role)}
