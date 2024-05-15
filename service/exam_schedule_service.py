from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status
from repository.exam_schedule_repository import ExamScheduleRepository
from typing import List, Optional
from schemas.exam_schedule import ExamScheduleBase, CreateExamSchedule, GetExamSchedule
from schemas.user import TokenPayload

MAX_RESERVATION_NUM = 50000


class ExamScheduleService:
    def __init__(self, session: Session):
        self.repository = ExamScheduleRepository(session)

    def get_schedules(self, current_user: TokenPayload) -> List[Optional[GetExamSchedule]]:
        if current_user['role'] == 'admin':
            exam_schedules = self.repository.get_all()
        else:
            exam_schedules = self.repository.get_available_schedules(current_user.id)

        schedules_with_remain_slot = []

        for exam_schedule in exam_schedules:
            confirmed_schedule_num = ExamScheduleRepository().get_confirmed_schedule_num(exam_schedule.id)

            schedules_with_remain_slot.append(GetExamSchedule(
                name=exam_schedule.name,
                start_time=exam_schedule.start_time,
                end_time=exam_schedule.end_time,
                remain_slot=MAX_RESERVATION_NUM - confirmed_schedule_num
            ))

        return schedules_with_remain_slot

    def create_schedule(self, current_user: TokenPayload, new_schedule: CreateExamSchedule) -> ExamScheduleBase:
        if current_user['role'] != 'admin':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can make exam schedules")

        if self.repository.exam_schedule_exist_by_name(new_schedule.name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Exam schedule's name must be unique. Please use other name.")

        return self.repository.create(new_schedule)
