from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from repository.exam_schedule_repository import ExamScheduleRepository
from repository.reservation_repository import ReservationRepository
from starlette import status

from repository.user_repository import UserRepository
from schemas.user import TokenPayload
from schemas.reservation import MakeEditReservationOutput, MakeEditReservationInput, ReservationBase
from service.exam_schedule_service import MAX_RESERVATION_NUM


class ReservationService:
    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)
        self.reservation_repository = ReservationRepository(session)
        self.exam_schedule_repository = ExamScheduleRepository(session)

    def make_reservation(self, current_user: TokenPayload, new_reservation: MakeEditReservationInput,
                         exam_schedule_id: int) -> MakeEditReservationOutput:
        if current_user['role'] != 'client':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only clients can make reservations")

        if not self.exam_schedule_repository.get_by_id(exam_schedule_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam schedule not found")

        if self.reservation_repository.get_by_user_id(current_user['id']):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="User already has a reservation for this exam schedule")

        if self.reservation_repository.get_confirmed_schedule_num(exam_schedule_id) >= MAX_RESERVATION_NUM:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Exam schedule has reached maximum reservations")

        return self.reservation_repository.create(ReservationBase(
            user_id=current_user['id'],
            exam_schedule_id=exam_schedule_id,
            comment=new_reservation.comment,
            confirmed=False,
        ))

    def get_my_reservation(self, current_user: TokenPayload) -> List[Optional[ReservationBase]]:
        if current_user['role'] != 'client':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Only clients can view their reservations")

        return self.reservation_repository.get_by_user_id(current_user['id'])

    def get_user_reservation(self, current_user: TokenPayload, user_id: int) -> List[Optional[ReservationBase]]:
        if current_user['role'] != 'admin':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can view user reservations")

        if not self.user_repository.exist_by_id(user_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with {user_id} not found")

        return self.reservation_repository.get_by_user_id(user_id)