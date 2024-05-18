from sqlalchemy.orm import Session
from db.models import User
from schemas.user import UserBase, LoginUser
from typing import List, Optional, Type


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Optional[UserBase]]:
        users = self.session.query(User).all()
        return [UserBase(**user.__dict__) for user in users]

    def get_by_user_id_role(self, user_id, role) -> List[Optional[UserBase]]:
        users = self.session.query(User).filter(
            User.user_id.contains(user_id),
            User.role.contains(role)
        )
        return [UserBase(**user.__dict__) for user in users]

    def get_by_user_id_password(self, user_id, password) -> Optional[UserBase]:
        user = self.session.query(User).filter_by(user_id=user_id, password=password).first()
        return user

    def exist_by_id(self, _id: int) -> bool:
        user = self.session.query(User).filter_by(id=_id)
        return user is not None
