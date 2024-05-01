from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    model_config = ConfigDict(extra='ignore')
    user_id: str
    password: str
    role: str


class LoginUser(BaseModel):
    model_config = ConfigDict(extra='ignore')

    user_id: str
    password: str

