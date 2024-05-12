from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.schema import PrimaryKeyConstraint

from db.database import Base


class User(Base):
    """
    유저를 나타내는 클래스입니다. 유저가 클라이언트인지 어드민인지는 `role` 필드로 구분합니다
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # client / admin

    reservations = relationship('Reservation', back_populates='user')


class ExamSchedule(Base):
    """
    시험 일정을 나타내는 클래스입니다.
    """
    __tablename__ = 'exam_schedules'

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False, unique=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    reservations = relationship('Reservation', back_populates='schedule')


class Reservation(Base):
    """
    시험 일정 예약 신청을 나타내는 클래스입니다. 예약의 확정 여부는 `confirmed` 필드로 구분합니다.
    """
    __tablename__ = 'reservations'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    user = relationship('User', back_populates='reservations')
    exam_schedule_id = Column(Integer, ForeignKey('exam_schedules.id'), primary_key=True)
    schedule = relationship('ExamSchedule', back_populates='reservations')
    comment = Column(Text, nullable=False, default='')
    confirmed = Column(Boolean, nullable=False, default=False)

    # composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'exam_schedule_id'),
    )
