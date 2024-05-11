import datetime

from pydantic import BaseModel, ConfigDict, FutureDatetime, Field


class ExamScheduleBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: int
    name: str
    date_time: datetime.datetime


class CreateExamSchedule(BaseModel):
    model_config = ConfigDict(extra='ignore')

    name: str = Field(description='시험 이름', examples=['Exam 1'])
    date_time: FutureDatetime = Field(description='시험 날짜', examples=['2025-02-20 12:30'])


class GetExamSchedule(ExamScheduleBase):
    remain_slot: int