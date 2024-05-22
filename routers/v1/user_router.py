from fastapi import APIRouter, Depends, Query
from db.database import get_db
from typing import List, Annotated
from schemas import user
from sqlalchemy.orm import Session

from service.user_service import UserService

user_router = APIRouter(
    prefix='/users',
    tags=['유저']
)


@user_router.get('/', response_model=List[user.UserBase], name='유저 검색')
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
    user_service = UserService(db)
    return user_service.search_users(user_id, role)


@user_router.post('/login', name='로그인', responses={
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
def login(login_user: user.LoginUser, db: Session = Depends(get_db)):
    """
    입력한 `user_id`와 `password`로 로그인을 합니다.
    로그인에 성공할 경우 jwt token을 반환합니다. token의 유효기간은 생성일부터 24시간까지 입니다.
    """
    user_service = UserService(db)
    return user_service.login(login_user)
