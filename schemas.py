import datetime

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    model_config = ConfigDict(extra='ignore')
    user_id: str
    role: str


class LoginUser(BaseModel):
    model_config = ConfigDict(extra='ignore')

    user_id: str
    password: str


class TokenPayload(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: str
    user_id: str
    role: str
    exp: int


class ExamScheduleBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: str
    name: str
    date_time: datetime.datetime


class GetExamSchedule(ExamScheduleBase):
    remain_slot: int


class ReservationBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: int
    user_id: int
    exam_schedule_id: int
    confirmed: bool
