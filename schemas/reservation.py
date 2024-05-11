import datetime

from pydantic import BaseModel, ConfigDict, FutureDatetime, Field


class ReservationBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: int
    user_id: int
    exam_schedule_id: int
    comment: str
    confirmed: bool


class MakeEditReservation(BaseModel):
    model_config = ConfigDict(extra='ignore')

    comment: str = Field(description='예약 신청의 코멘트', examples=['코멘트'])