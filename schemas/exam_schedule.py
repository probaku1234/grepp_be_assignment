import datetime

from pydantic import BaseModel, ConfigDict, FutureDatetime, Field, field_validator, model_validator
from pydantic_core.core_schema import FieldValidationInfo
from typing_extensions import Self


class ExamScheduleBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: int
    name: str
    start_time: datetime.datetime
    end_time: datetime.datetime

    @model_validator(mode='after')
    def validate_start_time_end_time(self) -> Self:
        start_time = self.start_time
        end_time = self.end_time
        if end_time <= start_time:
            raise ValueError('end time must be greater than the start time')

        return self


class CreateExamSchedule(BaseModel):
    model_config = ConfigDict(extra='ignore')

    name: str = Field(description='시험 이름', examples=['Exam 1'])
    start_time: FutureDatetime = Field(description='시험 날짜', examples=['2025-02-20 12:30'])
    end_time: FutureDatetime = Field(description='시험 날짜', examples=['2025-02-20 12:30'])

    @field_validator('end_time')
    @classmethod
    def validate_start_time_end_time(cls, value: datetime.datetime, info: FieldValidationInfo,
                                     **kwargs) -> datetime.datetime:
        start_date = info.data['start_time']

        if value <= start_date:
            raise ValueError("end time must be greater than the start time")

        return value


class GetExamSchedule(BaseModel):
    model_config = ConfigDict(extra='ignore')

    name: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    remain_slot: int
