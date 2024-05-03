import datetime
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.params import Path
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


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return decode_jwt(token)


# FIXME: if slot 0, exclude
@exam_router.get('/', dependencies=[Depends(JWTBearer())], response_model=List[schemas.GetExamSchedule])
def get_exam_schedules(current_user: Annotated[TokenPayload, Depends(get_current_user)], db: Session = Depends(get_db)):
    """
    시험 일정들과 각 일정들의 남아있는 예약 슬롯을 반환합니다.
    고객의 경우, 예약이 가능한 시험 일정만을 반환합니다. 이미 예약한 시험의 경우 결과에서 제외됩니다.
    어드민의 경우, 모든 시험 일정들을 반환합니다.
    """
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


@exam_router.post('/', dependencies=[Depends(JWTBearer())], status_code=status.HTTP_201_CREATED,
                  response_model=schemas.ExamScheduleBase, responses={
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
def create_exam_schedule(create_schedule: schemas.CreateExamSchedule,
                         current_user: Annotated[TokenPayload, Depends(get_current_user)],
                         db: Session = Depends(get_db)):
    """
    새로운 시험 일정을 만듭니다. 시험의 이름은 반드시 고유해야 하며, 시험 날짜는 현재보다 이후의 시간이여야 합니다.
    어드민 전용 API 입니다.
    """
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can make exam schedules")

    exam_schedule = db.query(models.ExamSchedule).filter(models.ExamSchedule.name == create_schedule.name).first()
    if exam_schedule:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Exam schedule's name must be unique. Please use other name.")

    new_exam_schedule = models.ExamSchedule(
        name=create_schedule.name,
        date_time=create_schedule.date_time
    )
    db.add(new_exam_schedule)
    db.commit()
    db.refresh(new_exam_schedule)

    return new_exam_schedule


# FIXME: output schema
@exam_router.post('/make_reservation/{exam_schedule_id}', dependencies=[Depends(JWTBearer())],
                  status_code=status.HTTP_201_CREATED, response_model=schemas.ReservationBase, responses={
        404: {
            "description": "`exam_schedule_id`값을 가진 시험 일정이 없는 경우",
            "content": {
                "application/json": {
                    "example": {"detail": "Exam schedule not found"}
                }
            }
        },
        400: {
            "description": "해당 유저가 이미 예약 신청을 했거나 남은 슬롯이 없는 경우",
            "content": {
                "application/json": {
                    "example": {"detail": "User already has a reservation for this exam schedule"}
                }
            }
        },
        403: {
            "description": "현재 유저가 admin인 경우",
            "content": {
                "application/json": {
                    "example": {"detail": "Only clients can make reservations"}
                }
            }
        }
    })
def make_reservation(current_user: Annotated[TokenPayload, Depends(get_current_user)],
                     make_reservation_request: schemas.MakeReservation,
                     db: Session = Depends(get_db),
                     exam_schedule_id: int = Path(..., description='예약을 신청할 시험 일정의 `id`')):
    """
    특정 시험에 예약을 신청합니다.
    고객 전용 API 입니다.
    """
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
        exam_schedule_id=exam_schedule_id,
        comment=make_reservation_request.comment
    )
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    return new_reservation


@exam_router.get('/my_reservation', dependencies=[Depends(JWTBearer())], response_model=List[schemas.ReservationBase],
                 responses={
                     403: {
                         "description": "현재 유저가 admin인 경우",
                         "content": {
                             "application/json": {
                                 "example": {"detail": "Only clients can view their reservations"}
                             }
                         }
                     }
                 })
def get_my_reservations(current_user: Annotated[TokenPayload, Depends(get_current_user)],
                        db: Session = Depends(get_db)):
    """
    현재 유저가 신청한 모든 예약 일정을 반환합니다.
    고객 전용 API 입니다.
    """
    if current_user['role'] != 'client':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only clients can view their reservations")

        # Retrieve the reservations for the current user
    reservations = db.query(models.Reservation).filter(models.Reservation.user_id == current_user['id']).all()

    return reservations


@exam_router.get('/user_reservation/{user_id}', dependencies=[Depends(JWTBearer())],
                 response_model=List[schemas.ReservationBase], responses={
        400: {
            "description": "`user_id`값을 가진 유저가 없는 경우",
            "content": {
                "application/json": {
                    "example": {"detail": "User with `user_id` not found"}
                }
            }
        },
        403: {
            "description": "현재 유저가 client인 경우",
            "content": {
                "application/json": {
                    "example": {"detail": "Only admins can view user reservations"}
                }
            }
        }
    })
def get_user_reservations(current_user: Annotated[TokenPayload, Depends(get_current_user)],
                          db: Session = Depends(get_db),
                          user_id: int = Path(..., description='예약 신청 목록을 조회할 유저의 `id`')):
    """
    특정 유저가 신청한 모든 예약 일정을 반환합니다.
    어드민 전용 API 입니다.
    """
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can view user reservations")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with {user_id} not found")

        # Retrieve the reservations for the specified user_id
    reservations = db.query(models.Reservation).filter(models.Reservation.user_id == user_id).all()

    return reservations


@exam_router.put('/confirm_reservation/{reservation_id}', dependencies=[Depends(JWTBearer())], responses={
    200: {
        "content": {
            "application/json": {
                "example": {"message": "Reservation confirmed successfully"}
            }
        }
    },
    404: {
        "description": "`reservation_id`값을 가진 예약이 없는 경우",
        "content": {
            "application/json": {
                "example": {"message": "Reservation not found"}
            }
        }
    },
    400: {
        "description": "예약이 이미 확정된 경우",
        "content": {
            "application/json": {
                "example": {"message": "Reservation already confirmed"}
            }
        }
    },
    403: {
        "description": "현재 유저가 client인 경우",
        "content": {
            "application/json": {
                "example": {"message": "Only admins can confirm reservations"}
            }
        }
    }
})
def confirm_reservation(current_user: Annotated[TokenPayload, Depends(get_current_user)],
                        db: Session = Depends(get_db),
                        reservation_id: int = Path(..., description='확정할 예약 신청의 `id`')):
    """
    고객이 신청한 예약을 확정합니다.
    어드민 전용 API 입니다.
    """
    # Check if the current user is an admin
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can confirm reservations")

    # Retrieve the reservation from the database
    reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()

    # Check if the reservation exists
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    # Check if the reservation is already confirmed
    if reservation.confirmed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reservation already confirmed")

    # Update the reservation to set confirmed to True
    reservation.confirmed = True
    db.commit()

    # Return a message indicating successful confirmation
    return {"message": "Reservation confirmed successfully"}


@exam_router.delete('/delete_reservation/{reservation_id}', dependencies=[Depends(JWTBearer())], responses={
    200: {
        "content": {
            "application/json": {
                "example": {"message": "Reservation deleted successfully"}
            }
        }
    },
    404: {
        "description": "`reservation_id`값을 가진 예약이 없는 경우",
        "content": {
            "application/json": {
                "example": {"message": "Reservation not found"}
            }
        }
    },
    403: {
        "description": "클라이언트 유저가 본인이 신청하지 않은 예약이나 이미 확정된 예약을 삭제할려는 경우, 어드민 유저가 이미 확정된 예약을 삭제할려는 경우",
        "content": {
            "application/json": {
                "example": {"message": "Cannot delete this reservation"}
            }
        }
    }
})
def delete_reservation(current_user: Annotated[TokenPayload, Depends(get_current_user)],
                       db: Session = Depends(get_db), reservation_id: int = Path(..., description='삭제할 예약 신청의 `id`')):
    """
    특정 시험 예약을 삭제합니다. 아직 확정되지 않은 예약만 삭제 가능합니다.
    고객의 경우, 오직 본인이 신청한 예약만 삭제할 수 있습니다.
    어드민의 경우, 모든 유저들의 예약을 삭제할 수 있습니다.
    """
    # Retrieve the reservation from the database
    reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()

    # Check if the reservation exists
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    # Check if the user is a client
    if current_user['role'] == 'client':
        # Check if the reservation belongs to the current user and is not confirmed
        if reservation.user_id != int(current_user['id']) or reservation.confirmed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete this reservation")
    else:  # If the user is an admin
        # Check if the reservation is confirmed
        if reservation.confirmed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete confirmed reservation")

    # Delete the reservation from the database
    db.delete(reservation)
    db.commit()

    return {"message": "Reservation deleted successfully"}
