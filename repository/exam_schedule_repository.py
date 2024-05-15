from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional, Type
from db.models import ExamSchedule, Reservation
from schemas.exam_schedule import ExamScheduleBase, CreateExamSchedule
import datetime


class ExamScheduleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Optional[ExamScheduleBase]]:
        exam_schedules = self.session.query(ExamSchedule).all()
        return [ExamScheduleBase(**exam_schedule.__dict__) for exam_schedule in exam_schedules]

    def get_by_id(self, _id) -> Optional[ExamScheduleBase]:
        exam_schedule = self.session.query(ExamSchedule).filter_by(id=_id).first()
        return exam_schedule

    def get_available_schedules(self, current_user_id: int) -> List[Optional[ExamScheduleBase]]:
        date_range_start = datetime.datetime.now(datetime.UTC)
        date_range_end = date_range_start + datetime.timedelta(days=3)
        exam_schedules = self.session.query(ExamSchedule) \
            .filter(ExamSchedule.start_time.between(date_range_start, date_range_end),
                    ~ExamSchedule.reservations.any(Reservation.user_id == current_user_id)).all()

        return [ExamScheduleBase(**exam_schedule.__dict__) for exam_schedule in exam_schedules]

    def create(self, data: CreateExamSchedule) -> ExamScheduleBase:
        exam_schedule = ExamSchedule(**data.model_dump(exclude_none=True))
        self.session.add(exam_schedule)
        self.session.commit()
        self.session.refresh(exam_schedule)

        return ExamScheduleBase(
            id=exam_schedule.id,
            name=exam_schedule.name,
            start_time=exam_schedule.start_time,
            end_time=exam_schedule.end_time
        )

    def exam_schedule_exist_by_name(self, name: str) -> bool:
        exam_schedule = self.session.query(ExamSchedule).filter_by(name=name).first()
        return exam_schedule is not None
