import datetime

from pydantic import BaseModel, ConfigDict, FutureDatetime, Field


class UserBase(BaseModel):
    model_config = ConfigDict(extra='ignore')
    user_id: int
    role: str


class LoginUser(BaseModel):
    model_config = ConfigDict(extra='ignore')

    user_id: int
    password: str


class TokenPayload(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: int
    user_id: str
    role: str
    exp: int
