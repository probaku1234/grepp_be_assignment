import hashlib

from fastapi import APIRouter, HTTPException, Depends, Query
from database import get_db
from typing import List, Annotated
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
    """
    유저의 비밀번호를 암호화하는 함수입니다.
    :param password:
    :return:
    """
    md5 = hashlib.md5()

    md5.update(password.encode('utf-8'))

    encrypted_password = md5.hexdigest()

    return encrypted_password


@user_router.get('/', response_model=List[schemas.UserBase])
def get_users(db: Session = Depends(get_db), user_id:
Annotated[
    str | None,
    Query(
        title="유저 아이디",
        description="db에서 검색을 위한 유저 아이디. 해당 값을 포함하는 `user_id`를 가진 유저를 반환합니다",
    ),
] = None
              , role:
        Annotated[
            str | None,
            Query(
                title="유저 role",
                description="db에서 검색을 위한 유저의 role. admin/ client 둘중 하나의 값을 전달해주세요.",
            ),
        ] = None
              ):
    """
    유저들의 리스트를 반환합니다. `user_id`와 `role`을 통해 검색할 수 있습니다. 만약 파라미터가 주어지지 않는다면 모든 유저들을 반환합니다. 테스트용 API 입니다.
    """
    user_id = user_id if user_id else ""
    if role:
        users = db.query(models.User).filter(
            models.User.user_id.contains(user_id), models.User.role == role
        )
    else:
        users = db.query(models.User).filter(
            models.User.user_id.contains(user_id)
        )

    return users


@user_router.post('/login', responses={
    200: {
        "description": "JWT token",
        "content": {
            "application/json": {
                "example": {"token": "token"}
            }
        }
    },
    400: {
        "description": "잘못된 로그인 정보",
        "content": {
            "application/json": {
                "example": {"detail": "The id or password is not right"}
            }
        }
    }
})
def login(login_user: schemas.LoginUser, db: Session = Depends(get_db)):
    """
    입력한 `user_id`와 `password`로 로그인을 합니다.
    로그인에 성공할 경우 jwt token을 반환합니다. token의 유효기간은 생성일부터 24시간까지 입니다.
    """
    user = db.query(models.User).filter(
        models.User.user_id == login_user.user_id and models.User.password == _encrypt_password(
            login_user.password)).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The id or password is not right")

    # create jwt token and return
    return {'token': encode_jwt(user.id, user.user_id, user.role)}
