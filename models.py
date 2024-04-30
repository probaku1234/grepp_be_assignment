from database import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, text


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(String, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
