import datetime
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Depends
from fastapi.params import Path
from sqlalchemy.orm import Session
from starlette import status

from auth.auth_bearer import JWTBearer
from db import models
from db.database import get_db
from schemas import reservation, user, base
from service.reservation_service import ReservationService
from util import get_current_user

reservation_router = APIRouter(
    prefix='/reservation',
    tags=['시험 일정']
)


@reservation_router.post('/make_reservation/{exam_schedule_id}',
                         dependencies=[Depends(JWTBearer())],
                         status_code=status.HTTP_201_CREATED,
                         response_model=reservation.ReservationBase,
                         name='시험 일정 예약신청',
                         responses={
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
                         }
                         )
def make_reservation(current_user: Annotated[user.TokenPayload, Depends(get_current_user)],
                     make_reservation_request: reservation.MakeEditReservationInput,
                     db: Session = Depends(get_db),
                     exam_schedule_id: int = Path(..., description='예약을 신청할 시험 일정의 `id`')):
    """
    특정 시험에 예약을 신청합니다.
    고객 전용 API 입니다.
    """
    reservation_service = ReservationService(db)
    return reservation_service.make_reservation(current_user, make_reservation_request, exam_schedule_id)


@reservation_router.get('/my_reservation',
                        dependencies=[Depends(JWTBearer())],
                        name='내 예약 신청 조회',
                        response_model=List[reservation.ReservationBase],
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
def get_my_reservations(current_user: Annotated[user.TokenPayload, Depends(get_current_user)],
                        db: Session = Depends(get_db)):
    reservation_service = ReservationService(db)
    return reservation_service.get_my_reservation(current_user)


@reservation_router.get('/user_reservation/{user_id}',
                        dependencies=[Depends(JWTBearer())],
                        response_model=List[reservation.ReservationBase],
                        name='예약 신청 조회',
                        responses={
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
def get_user_reservations(current_user: Annotated[user.TokenPayload, Depends(get_current_user)],
                          db: Session = Depends(get_db),
                          user_id: int = Path(..., description='예약 신청 목록을 조회할 유저의 `id`')):
    reservation_service = ReservationService(db)
    return reservation_service.get_user_reservation(current_user, user_id)


@reservation_router.put('/confirm_reservation',
                        dependencies=[Depends(JWTBearer())],
                        name='예약 신청 확정',
                        response_model=base.MessageOutputBase,
                        responses={
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
def confirm_reservation(current_user: Annotated[user.TokenPayload, Depends(get_current_user)],
                        confirm_reservation_request: reservation.ConfirmReservationRequest,
                        db: Session = Depends(get_db)
                        ):
    reservation_service = ReservationService(db)
    return reservation_service.confirm_reservation(current_user, confirm_reservation_request)


@reservation_router.put('/edit_my_reservation', dependencies=[Depends(JWTBearer())], name='예약 신청 수정', responses={
    200: {
        "content": {
            "application/json": {
                "example": {"message": "Reservation comment updated successfully"}
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
                "example": {"message": "Cannot edit confirmed reservation"}
            }
        }
    },
    403: {
        "description": "현재 유저가 client인 경우",
        "content": {
            "application/json": {
                "example": {"message": "Cannot edit other users' reservations"}
            }
        }
    }
})
def edit_my_reservation(current_user: Annotated[user.TokenPayload, Depends(get_current_user)],
                        edit_reservation_request: reservation.EditReservationClientInput,
                        db: Session = Depends(get_db)
                        ):
    reservation_service = ReservationService(db)
    return reservation_service.edit_reservation(current_user, current_user['id'],
                                                edit_reservation_request.exam_schedule_id,
                                                edit_reservation_request.comment)


@reservation_router.put('/edit_user_reservation', dependencies=[Depends(JWTBearer())], name='예약 신청 수정', responses={
    200: {
        "content": {
            "application/json": {
                "example": {"message": "Reservation comment updated successfully"}
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
                "example": {"message": "Cannot edit confirmed reservation"}
            }
        }
    },
    403: {
        "description": "현재 유저가 client인 경우",
        "content": {
            "application/json": {
                "example": {"message": "Cannot edit other users' reservations"}
            }
        }
    }
})
def edit_my_reservation(current_user: Annotated[user.TokenPayload, Depends(get_current_user)],
                        edit_reservation_request: reservation.EditReservationAdminInput,
                        db: Session = Depends(get_db)
                        ):
    reservation_service = ReservationService(db)
    return reservation_service.edit_reservation(current_user, edit_reservation_request.user_id,
                                                edit_reservation_request.exam_schedule_id,
                                                edit_reservation_request.comment)