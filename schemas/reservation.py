from pydantic import BaseModel, ConfigDict, Field


class ReservationBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

    user_id: int
    exam_schedule_id: int
    comment: str
    confirmed: bool


class MakeEditReservationInput(BaseModel):
    model_config = ConfigDict(extra='allow')

    comment: str = Field(description='예약 신청의 코멘트', examples=['코멘트'])


class EditReservationClientInput(MakeEditReservationInput):
    exam_schedule_id: int


class MakeEditReservationOutput(BaseModel):
    model_config = ConfigDict(extra='ignore')

    exam_schedule_id: int
    comment: str
    confirmed: bool


class ConfirmReservationRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')

    user_id: int
    exam_schedule_id: int

