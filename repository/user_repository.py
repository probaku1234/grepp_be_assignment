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

    def get_by_user_id_role(self):
        pass

    def user_exists_by_user_id_password(self, user_id, password) -> bool:
        user = self.session.query(User).filter_by(user_id=user_id, password=password).first()
        return user is not None
