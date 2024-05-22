from sqlalchemy import func
from sqlalchemy.orm import Session
from db.models import Reservation
from typing import List, Optional, Type

from schemas.reservation import MakeEditReservationOutput, ReservationBase, MakeEditReservationInput


class ReservationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, _id: int) -> Type[Reservation]:
        reservation = self.session.query(Reservation).filter_by(id=_id).first()

        return reservation

    def get_by_user_id(self, user_id: int) -> List[Optional[ReservationBase]]:
        reservations = self.session.query(Reservation).filter_by(user_id=user_id)
        return [ReservationBase(**reservation.__dict__) for reservation in reservations]

    def get_by_user_id_exam_id(self, exam_schedule_id: int, user_id: int) -> Type[Reservation]:
        reservation = self.session.query(Reservation).filter_by(user_id=user_id,
                                                                exam_schedule_id=exam_schedule_id).first()
        return reservation

    def exist_by_user_id_exam_id(self, exam_schedule_id: int, user_id: int) -> bool:
        reservation = self.session.query(Reservation).filter_by(user_id=user_id, exam_schedule_id=exam_schedule_id)
        return reservation is not None

    def get_confirmed_schedule_num(self, exam_schedule_id) -> int:
        return self.session.query(func.count(Reservation.user_id)) \
            .filter(Reservation.exam_schedule_id == exam_schedule_id,
                    Reservation.confirmed.is_(True)) \
            .scalar() or 0

    def create(self, data: ReservationBase) -> MakeEditReservationOutput:
        reservation = Reservation(**data.model_dump(exclude_none=True))
        self.session.add(reservation)
        self.session.commit()
        self.session.refresh(reservation)

        return MakeEditReservationOutput(
            exam_schedule_id=reservation.exam_schedule_id,
            comment=reservation.comment,
            confirmed=reservation.confirmed
        )

    def update(self, reservation: Type[Reservation], data: MakeEditReservationInput):
        data_dict = data.dict()
        if 'confirmed' in data_dict:
            reservation.confirmed = data_dict['confirmed']

        reservation.comment = data_dict['comment']
        self.session.commit()
        self.session.refresh(reservation)

    def delete(self, reservation: Type[Reservation]):
        self.session.delete(reservation)
        self.session.commit()
