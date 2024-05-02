import datetime
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, text, or_
from fastapi.security import OAuth2PasswordBearer
from starlette import status

import models
import schemas
from database import get_db
from auth.auth_bearer import JWTBearer
from schemas import TokenPayload
from util import decode_jwt

MAX_RESERVATION_NUM = 50000

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

exam_router = APIRouter(
    prefix='/exam_schedule',
    tags=['Exam Schedules']
)


# FIXME: token save user id so no query needed
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return decode_jwt(token)


@exam_router.get('/', dependencies=[Depends(JWTBearer())], response_model=List[schemas.GetExamSchedule])
def get_exam_schedules(current_user: Annotated[TokenPayload, Depends(get_current_user)], db: Session = Depends(get_db)):
    if current_user['role'] == 'admin':
        # Fetch all exam schedules for admin
        exam_schedules = db.query(models.ExamSchedule).all()
    else:
        # Fetch current user's ID
        # current_user_id = db.query(models.User.id).filter(models.User.user_id == current_user['user_id']).scalar()

        # Fetch exam schedules not reserved by the current user and within 3 days from now
        exam_schedules = db.query(models.ExamSchedule) \
            .filter(models.ExamSchedule.date_time < func.now() + datetime.timedelta(days=3)) \
            .outerjoin(models.Reservation,
                       (models.ExamSchedule.id == models.Reservation.exam_schedule_id) & (
                               models.Reservation.user_id == current_user['id'])) \
            .filter(or_(models.Reservation.id == None, models.Reservation.user_id != current_user['id'])) \
            .all()

        # Initialize schedules list
    schedules = []

    for exam_schedule in exam_schedules:
        # Count confirmed reservations for the exam schedule
        confirmed_schedule_num = db.query(func.count(models.Reservation.id)) \
                                     .filter(models.Reservation.exam_schedule_id == exam_schedule.id,
                                             models.Reservation.confirmed.is_(True)) \
                                     .scalar() or 0

        # Append exam schedule to schedules list
        schedules.append(schemas.GetExamSchedule(
            id=str(exam_schedule.id),
            name=exam_schedule.name,
            date_time=exam_schedule.date_time,
            remain_slot=MAX_RESERVATION_NUM - confirmed_schedule_num
        ))

    return schedules

# out of range?
@exam_router.post('/make_reservation/{exam_schedule_id}', dependencies=[Depends(JWTBearer())],
                  status_code=status.HTTP_201_CREATED)
def make_reservation(exam_schedule_id: int, current_user: Annotated[TokenPayload, Depends(get_current_user)],
                     db: Session = Depends(get_db)):
    if current_user['role'] != 'client':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only clients can make reservations")

    exam_schedule = db.query(models.ExamSchedule).filter(models.ExamSchedule.id == exam_schedule_id).first()
    if not exam_schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam schedule not found")

    existing_reservation = db.query(models.Reservation).filter(
        models.Reservation.exam_schedule_id == exam_schedule_id,
        models.Reservation.user_id == current_user['id']
    ).first()

    if existing_reservation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="User already has a reservation for this exam schedule")

    exam_schedule_reservations_count = db.query(models.Reservation).filter(
        models.Reservation.exam_schedule_id == exam_schedule_id,
        models.Reservation.confirmed.is_(True)
    ).count()

    if exam_schedule_reservations_count >= MAX_RESERVATION_NUM:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Exam schedule has reached maximum reservations")

    # Create a new reservation
    new_reservation = models.Reservation(
        user_id=current_user['id'],
        exam_schedule_id=exam_schedule_id
    )
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    return new_reservation


@exam_router.get('/my_reservation', dependencies=[Depends(JWTBearer())])
def get_my_reservations(current_user: Annotated[TokenPayload, Depends(get_current_user)],
                        db: Session = Depends(get_db)):
    pass


@exam_router.get('/user_reservation/{user_id}', dependencies=[Depends(JWTBearer())])
def get_user_reservations(user_id: int, current_user: Annotated[TokenPayload, Depends(get_current_user)],
                          db: Session = Depends(get_db)):
    pass


@exam_router.put('/confirm_reservation/{reservation_id}', dependencies=[Depends(JWTBearer())])
def confirm_reservation(reservation_id: int, current_user: Annotated[TokenPayload, Depends(get_current_user)],
                        db: Session = Depends(get_db)):
    pass
