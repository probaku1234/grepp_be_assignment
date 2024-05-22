from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from starlette import status

from db.database import get_db
from auth.auth_bearer import JWTBearer
from schemas import exam_schedule, user
from service.exam_schedule_service import ExamScheduleService
from util import get_current_user

MAX_RESERVATION_NUM = 50000

exam_router = APIRouter(
    prefix='/exam_schedule',
    tags=['시험 일정']
)


@exam_router.get('/', dependencies=[Depends(JWTBearer())], response_model=List[exam_schedule.GetExamSchedule],
                 name='시험 일정 조회')
def get_exam_schedules(current_user: Annotated[user.TokenPayload, Depends(get_current_user)], db: Session = Depends(get_db)):
    """
    시험 일정들과 각 일정들의 남아있는 예약 슬롯을 반환합니다.
    고객의 경우, 예약이 가능한 시험 일정만을 반환합니다. 이미 예약한 시험이거나 시험 시간이 지난 경우 결과에서 제외됩니다.
    어드민의 경우, 모든 시험 일정들을 반환합니다.
    """
    exam_schedule_service = ExamScheduleService(db)
    return exam_schedule_service.get_schedules(current_user)


@exam_router.post('/', name='시험 일정 생성', dependencies=[Depends(JWTBearer())], status_code=status.HTTP_201_CREATED,
                  response_model=exam_schedule.ExamScheduleBase, responses={
        400: {
            "description": "주어진 `name`을 가진 시험 일정이 이미 존재하는 경우",
            "content": {
                "application/json": {
                    "example": {"message": "Exam schedule's name must be unique. Please use other name."}
                }
            }
        },
        403: {
            "description": "현재 유저가 client인 경우",
            "content": {
                "application/json": {
                    "example": {"message": "Only admin can make exam schedules"}
                }
            }
        }
    })
def create_exam_schedule(create_schedule: exam_schedule.CreateExamSchedule,
                         current_user: Annotated[user.TokenPayload, Depends(get_current_user)],
                         db: Session = Depends(get_db)):
    """
    새로운 시험 일정을 만듭니다. 시험의 이름은 반드시 고유해야 하며, 시험 날짜는 현재보다 이후의 시간이여야 합니다.
    어드민 전용 API 입니다.
    """
    exam_schedule_service = ExamScheduleService(db)
    return exam_schedule_service.create_schedule(current_user, create_schedule)
