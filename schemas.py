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


class TokenPayload(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: str
    user_id: str
    role: str
    exp: int


class ExamScheduleBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: int
    name: str
    date_time: datetime.datetime


class CreateExamSchedule(BaseModel):
    model_config = ConfigDict(extra='ignore')

    name: str = Field(description="시험 이름", examples=['Exam 1'])
    date_time: FutureDatetime = Field(description="시험 날짜", examples=['2025-02-20 12:30'])


class GetExamSchedule(ExamScheduleBase):
    remain_slot: int


class ReservationBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: int
    user_id: int
    exam_schedule_id: int
    comment: str
    confirmed: bool


class MakeEditReservation(BaseModel):
    model_config = ConfigDict(extra='ignore')

    comment: str = Field(description="예약 신청의 코멘트", examples=['코멘트'])
