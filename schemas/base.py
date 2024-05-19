from pydantic import BaseModel, ConfigDict


class MessageOutputBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

    message: str
