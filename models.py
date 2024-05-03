from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # client / admin

    reservations = relationship('Reservation', back_populates='user')


class ExamSchedule(Base):
    __tablename__ = 'exam_schedules'

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False, unique=True)
    date_time = Column(DateTime, nullable=False)

    reservations = relationship('Reservation', back_populates='schedule')


class Reservation(Base):
    __tablename__ = 'reservations'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='reservations')
    exam_schedule_id = Column(Integer, ForeignKey('exam_schedules.id'))
    schedule = relationship('ExamSchedule', back_populates='reservations')
    comment = Column(Text, nullable=False, default="")
    confirmed = Column(Boolean, nullable=False, default=False)
