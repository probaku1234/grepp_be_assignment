import datetime

from pydantic import BaseModel, ConfigDict, FutureDatetime, Field


class UserBase(BaseModel):
    model_config = ConfigDict(extra='ignore')
    user_id: str
    role: str


class LoginUser(BaseModel):
    model_config = ConfigDict(extra='ignore')

    user_id: str
    password: str


class LoginOutput(BaseModel):
    model_config = ConfigDict(extra='ignore')

    token: str


class TokenPayload(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: int
    user_id: str
    role: str
    exp: int
