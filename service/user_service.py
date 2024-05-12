import hashlib
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from schemas.user import UserBase, LoginUser, LoginOutput
from typing import List, Optional, Type
from repository.user_repository import UserRepository
from starlette import status

from util import encode_jwt


def _encrypt_password(password):
    """
    유저의 비밀번호를 암호화하는 함수입니다.
    """
    md5 = hashlib.md5()

    md5.update(password.encode('utf-8'))

    encrypted_password = md5.hexdigest()

    return encrypted_password


class UserService:
    def __init__(self, session: Session):
        self.repository = UserRepository(session)

    def get_all(self) -> List[Optional[UserBase]]:
        return self.repository.get_all()

    def search_users(self, user_id, role) -> List[Optional[UserBase]]:
        if not user_id and not role:
            return self.get_all()

        user_id = user_id if user_id else ""
        role = role if role else ""

        return self.repository.get_by_user_id_role(user_id, role)

    def login(self, login_user: LoginUser) -> LoginOutput:
        user = self.repository.get_by_user_id_password(login_user.user_id, _encrypt_password(login_user.password))

        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The id or password is not right")

        token = encode_jwt(user.id, user.user_id, user.role)
        return LoginOutput(token=token)