from pydantic import BaseModel


class UserBase(BaseModel):
    user_id: str
    password: str
    role: str

    class Config:
        from_attributes = True


