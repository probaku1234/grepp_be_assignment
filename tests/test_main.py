"""
각 endpoint의 test code 입니다.
"""

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv
import os
from typing import Tuple
import datetime

import models
from database import Base, get_db
from main import app
from models import Reservation, ExamSchedule
from routers.exam_router import MAX_RESERVATION_NUM
from util import encode_jwt, decode_jwt

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.environ.get('SQLALCHEMY_DATABASE_URL')

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


class UtilTest:
    def insert_user_data(data: Tuple):
        conn = engine.raw_connection()

        cursor = conn.cursor()
        query = 'INSERT OR IGNORE INTO users(id, user_id, password, role) VALUES (?, ?, ?, ?);'

        cursor.execute(query, data)
        conn.commit()

    def insert_exam_schedule_data(data: Tuple):
        conn = engine.raw_connection()

        cursor = conn.cursor()
        query = 'INSERT OR IGNORE INTO exam_schedules(id, name, date_time) VALUES (?, ?, ?);'

        cursor.execute(query, data)
        conn.commit()


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def test_db_with_users():
    Base.metadata.create_all(bind=engine)
    UtilTest.insert_user_data((1, 'user 1', '71b3b26aaa319e0cdf6fdb8429c112b0', 'client'))
    UtilTest.insert_user_data((2, 'admin 1', '71b3b26aaa319e0cdf6fdb8429c112b0', 'admin'))
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def test_db_with_users_and_exam_schedules():
    Base.metadata.create_all(bind=engine)
    UtilTest.insert_user_data((1, 'user 1', '71b3b26aaa319e0cdf6fdb8429c112b0', 'client'))
    UtilTest.insert_user_data((2, 'admin 1', '71b3b26aaa319e0cdf6fdb8429c112b0', 'admin'))
    UtilTest.insert_exam_schedule_data((1, 'exam 1', datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        days=1)))
    UtilTest.insert_exam_schedule_data((2, 'exam 2', datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        days=5)))
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

JWT_SECRET = os.environ.get('JWT_SECRET')


class TestUserRoute:
    def test_get_users_should_return_all_users_when_no_parameters_given(self, test_db_with_users):
        response = client.get(
            "/users"
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data == [{
            'role': 'client',
            'user_id': 'user 1'},
            {
                'role': 'admin',
                'user_id': 'admin 1'}]

    def test_get_users_should_return_users_with_matched(self, test_db_with_users):
        user_id_query = 'user'
        role_query = 'admin'

        response = client.get(
            f"/users?role={role_query}",
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data == [
            {
                'role': 'admin',
                'user_id': 'admin 1'}]

        response = client.get(
            f"/users?user_id={user_id_query}",
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data == [
            {
                'role': 'client',
                'user_id': 'user 1'}]

        response = client.get(
            f"/users?user_id={user_id_query}&role={role_query}",
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data == []

    def test_login_should_return_400_when_credential_not_correct(self, test_db_with_users):
        response = client.post(
            "/users/login",
            json={
                "user_id": 'invalid id',
                "password": '789456'
            }
        )
        assert response.status_code == 400, response.text

    def test_login_should_return_422_when_request_body_not_have_required_fields(self, test_db_with_users):
        response = client.post(
            "/users/login",
            json={
                "user_id": 'invalid id',
            }
        )
        assert response.status_code == 422, response.text

    def test_login_should_return_token_when_successful_login(self, test_db_with_users):
        user_id = 'user 1'
        response = client.post(
            "/users/login",
            json={
                "user_id": user_id,
                "password": '789456'
            }
        )
        assert response.status_code == 200, response.text
        data = response.json()

        assert 'token' in data.keys()

        token = data['token']

        payload = jwt.decode(token, JWT_SECRET, algorithms='HS256')
        assert payload['user_id'] == user_id


class TestExamRoute:
    class TestGetSchedules:
        def test_get_exam_schedules_should_return_403_with_no_token(self, test_db):
            response = client.get(
                "/exam_schedule",
            )

            assert response.status_code == 403, response.text

        def test_get_exam_schedules_should_return_403_with_invalid_token(self, test_db):
            response = client.get(
                "/exam_schedule",
                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        def test_get_exam_schedules_should_return_empty_list_with_no_exam_schedule_data(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            response = client.get(
                "/exam_schedule",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

            assert response.status_code == 200, response.text
            data = response.json()
            assert data == []

        def test_get_exam_schedules_should_return_all_exam_schedules_for_admin(self, test_db_with_users):
            token = encode_jwt('1', 'admin 1', 'admin')

            UtilTest.insert_exam_schedule_data((1, 'exam 1', datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=1)))
            UtilTest.insert_exam_schedule_data((2, 'exam 2', datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=5)))

            response = client.get(
                "/exam_schedule",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

            assert response.status_code == 200, response.text
            data = response.json()
            assert len(data) == 2

        def test_get_exam_schedules_should_return_exam_schedules_within_range_for_client(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            UtilTest.insert_exam_schedule_data((1, 'exam 1', datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=1)))
            UtilTest.insert_exam_schedule_data((2, 'exam 2', datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=5)))
            UtilTest.insert_exam_schedule_data((3, 'exam 3', datetime.datetime(2022, 2, 3)))

            response = client.get(
                "/exam_schedule",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

            assert response.status_code == 200, response.text
            data = response.json()
            assert len(data) == 1
            assert data[0]['name'] == 'exam 1'

        def test_get_exam_schedules_should_exclude_exam_schedules_if_already_reserved_for_client(self,
                                                                                                 test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            session = TestingSessionLocal()
            exam_schedule = ExamSchedule(name="Example Exam",
                                         date_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                             days=2))
            session.add(exam_schedule)

            session.commit()

            reservation = Reservation(user_id='1', exam_schedule_id=exam_schedule.id, confirmed=True)
            session.add(reservation)
            session.commit()

            response = client.get(
                "/exam_schedule",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

            assert response.status_code == 200, response.text
            data = response.json()
            assert len(data) == 0

        def test_get_exam_schedules_should_return_remain_slot(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            session = TestingSessionLocal()
            exam_schedule = ExamSchedule(name="Example Exam",
                                         date_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                             days=2))
            session.add(exam_schedule)

            session.commit()

            reservation = Reservation(user_id='2', exam_schedule_id=exam_schedule.id, confirmed=True)
            session.add(reservation)
            session.commit()

            response = client.get(
                "/exam_schedule",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

            assert response.status_code == 200, response.text
            data = response.json()
            assert len(data) == 1
            assert data[0]['remain_slot'] == 49999

    class TestCreateExamSchedule:
        def test_create_exam_schedule_should_return_403_with_no_token(self, test_db):
            response = client.post(
                "/exam_schedule",
            )

            assert response.status_code == 403, response.text

        def test_create_exam_schedule_should_return_401_with_invalid_token(self, test_db):
            response = client.post(
                "/exam_schedule",
                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        def test_create_exam_schedule_should_return_403_for_non_client_user(self, test_db_with_users):
            token = encode_jwt('1', 'client 1', 'client')

            response = client.post(
                "/exam_schedule",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": 'test test',
                    "date_time": '2025-02-20 12:30'
                }
            )

            assert response.status_code == 403

        def test_create_exam_schedule_should_return_422_when_past_date_given(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            response = client.post(
                "/exam_schedule",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": 'test test',
                    "date_time": '1990-02-20 12:30'
                }
            )

            assert response.status_code == 422, response.text
            assert response.json()['detail'][0]['msg'] == 'Input should be in the future'

        def test_create_exam_schedule_should_return_422_when_required_fields_not_given(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            response = client.post(
                "/exam_schedule",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "date_time": '1990-02-20 12:30'
                }
            )

            assert response.status_code == 422, response.text
            assert response.json()['detail'][0]['msg'] == 'Field required'

        def test_create_exam_schedule_should_return_400_when_name_alreay_exist(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            test_name = 'test test'
            session = TestingSessionLocal()
            new_exam_schedule = models.ExamSchedule(
                name=test_name,
                date_time=datetime.datetime.now(datetime.UTC)
            )
            session.add(new_exam_schedule)
            session.flush()

            response = client.post(
                "/exam_schedule",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": test_name,
                    "date_time": '2025-02-20 12:30'
                }
            )

            assert response.status_code == 400, response.text
            assert response.json()['detail'] == "Exam schedule's name must be unique. Please use other name."

        def test_create_exam_schedule_success(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            test_name = 'test test'
            test_date = '2025-02-20 12:30'

            response = client.post(
                "/exam_schedule",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": test_name,
                    "date_time": test_date
                }
            )

            assert response.status_code == 201, response.text

            session = TestingSessionLocal()
            created_exam_schedule = session.get(ExamSchedule, 1)
            assert created_exam_schedule.name == test_name
            assert created_exam_schedule.date_time == datetime.datetime.strptime(test_date, '%Y-%m-%d %H:%M')

    class TestMakeReservation:
        def test_make_reservation_should_return_403_with_no_token(self, test_db):
            response = client.post(
                "/exam_schedule/make_reservation/2",
            )

            assert response.status_code == 403, response.text

        def test_make_reservation_should_return_401_with_invalid_token(self, test_db):
            response = client.post(
                "/exam_schedule/make_reservation/2",
                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        def test_make_reservation_should_return_403_for_non_client_user(self, test_db_with_users):
            token = encode_jwt('1', 'admin 1', 'admin')

            response = client.post(
                "/exam_schedule/make_reservation/2",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    'comment': ""
                }
            )

            assert response.status_code == 403

        def test_make_reservation_should_return_400_when_user_already_has_reservation(self,
                                                                                      test_db_with_users_and_exam_schedules):
            token = encode_jwt('1', 'user 1', 'client')

            existing_reservation = Reservation(user_id='1', exam_schedule_id=1)
            session = TestingSessionLocal()

            session.add(existing_reservation)
            session.flush()

            response = client.post(
                "/exam_schedule/make_reservation/1",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    'comment': ""
                }
            )

            # Assert that the response status code is 400
            assert response.status_code == 400

        @pytest.mark.parametrize("exam_schedule_id", [1000, 999, -1])  # IDs that don't exist
        def test_make_reservation_exam_schedule_not_found(self, exam_schedule_id, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            response = client.post(
                f"/exam_schedule/make_reservation/{exam_schedule_id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    'comment': ""
                }
            )

            assert response.status_code == 404

            assert response.json() == {"detail": "Exam schedule not found"}

        def test_make_reservation_max_reservation_reached(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            exam_schedule = ExamSchedule(name="Example Exam", date_time=datetime.datetime.now(datetime.UTC))
            session = TestingSessionLocal()
            session.add(exam_schedule)

            session.commit()

            max_reservations = MAX_RESERVATION_NUM
            for i in range(max_reservations):
                reservation = Reservation(user_id='2', exam_schedule_id=exam_schedule.id, confirmed=True)
                session.add(reservation)

            session.commit()

            response = client.post(
                f"/exam_schedule/make_reservation/{exam_schedule.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    'comment': ""
                }
            )

            assert response.status_code == 400

            assert response.json() == {"detail": "Exam schedule has reached maximum reservations"}

        def test_make_reservation_success(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            exam_schedule = ExamSchedule(name="Example Exam", date_time=datetime.datetime.now(datetime.UTC))
            session = TestingSessionLocal()
            session.add(exam_schedule)

            session.commit()

            test_comment = "test comment"

            response = client.post(
                f"/exam_schedule/make_reservation/{exam_schedule.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    'comment': test_comment
                }
            )

            assert response.status_code == 201

            assert "user_id" in response.json()
            assert "exam_schedule_id" in response.json()
            assert "confirmed" in response.json()
            assert "comment" in response.json()
            assert response.json()["user_id"] == 1
            assert response.json()["exam_schedule_id"] == exam_schedule.id
            assert response.json()["comment"] == test_comment
            assert response.json()["confirmed"] is False

    class TestGetMyReservation:
        def test_my_reservation_should_return_403_with_no_token(self, test_db):
            response = client.get(
                "/exam_schedule/my_reservation",
            )

            assert response.status_code == 403, response.text

        def test_my_reservation_should_return_403_with_invalid_token(self, test_db):
            response = client.get(
                "/exam_schedule/my_reservation",

                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        def test_my_reservation_should_return_empty_list_with_no_reservation_data(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            response = client.get(
                "/exam_schedule/my_reservation",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

            assert response.status_code == 200, response.text
            data = response.json()
            assert data == []

        def test_my_reservation_should_return_403_when_admin(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            response = client.get(
                "/exam_schedule/my_reservation",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

            assert response.status_code == 403, response.text
            assert response.json()["detail"] == "Only clients can view their reservations"

        def test_my_reservation_should_return_current_user_reservations(self, test_db_with_users_and_exam_schedules):
            token = encode_jwt('1', 'user 1', 'client')

            session = TestingSessionLocal()
            reservations_data = [
                {"user_id": '1', "exam_schedule_id": '1'},
                {"user_id": '1', "exam_schedule_id": '2'}
            ]
            for reservation_data in reservations_data:
                reservation = Reservation(**reservation_data)
                session.add(reservation)
            session.flush()

            response = client.get(
                "/exam_schedule/my_reservation",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

            assert response.status_code == 200

            response_data = response.json()
            assert isinstance(response_data, list)
            assert len(response_data) == 2

            for item in response_data:
                assert "id" in item
                assert "user_id" in item
                assert "exam_schedule_id" in item

    class TestGetUserReservations:
        def test_get_user_reservations_should_return_403_with_no_token(self, test_db):
            response = client.get(
                "/exam_schedule/user_reservation/1",
            )

            assert response.status_code == 403, response.text

        def test_get_user_reservations_should_return_403_with_invalid_token(self, test_db):
            response = client.get(
                "/exam_schedule/user_reservation/1",

                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        def test_get_user_reservations_should_return_403_for_client(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            response = client.get(
                "/exam_schedule/user_reservation/1",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

            assert response.status_code == 403, response.text
            assert response.json()["detail"] == "Only admins can view user reservations"

        def test_get_user_reservations_should_return_400_when_user_not_found(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            invalid_user_id = 999
            response = client.get(
                f"/exam_schedule/user_reservation/{invalid_user_id}",
                # Using a user_id that doesn't exist in the test database
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 400

            assert response.json()["detail"] == f"User with {invalid_user_id} not found"

        def test_get_user_reservations_success(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            session = TestingSessionLocal()
            reservations_data = [
                {"user_id": 1, "exam_schedule_id": 1},
                {"user_id": 1, "exam_schedule_id": 2}
            ]
            for reservation_data in reservations_data:
                reservation = Reservation(**reservation_data)
                session.add(reservation)
            session.flush()

            response = client.get(
                "/exam_schedule/user_reservation/1",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200

            response_data = response.json()
            assert isinstance(response_data, list)
            assert len(response_data) == 2

    class TestConfirmReservations:
        def test_confirm_reservation_should_return_403_with_no_token(self, test_db):
            response = client.put(
                "/exam_schedule/confirm_reservation/1",
            )

            assert response.status_code == 403, response.text

        def test_confirm_reservation_should_return_403_with_invalid_token(self, test_db):
            response = client.put(
                "/exam_schedule/confirm_reservation/1",

                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        def test_confirm_reservation_should_return_403_for_client(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            response = client.put(
                "/exam_schedule/confirm_reservation/1",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

            assert response.status_code == 403, response.text
            assert response.json()["detail"] == "Only admins can confirm reservations"

        @pytest.mark.parametrize("reservation_id", [1000, 999, -1])
        def test_confirm_reservation_should_return_404_reservation_not_found(self, reservation_id, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            response = client.put(
                f"/exam_schedule/confirm_reservation/{reservation_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 404

            assert response.json()["detail"] == "Reservation not found"

        def test_confirm_reservation_already_confirmed(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            session = TestingSessionLocal()
            reservation = Reservation(user_id=2, exam_schedule_id=1, confirmed=True)
            session.add(reservation)
            session.flush()

            response = client.put(
                f"/exam_schedule/confirm_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 400

            assert response.json()["detail"] == "Reservation already confirmed"

        def test_confirm_reservation_success(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            session = TestingSessionLocal()
            reservation = Reservation(user_id=2, exam_schedule_id=1, confirmed=False)
            session.add(reservation)
            session.flush()

            response = client.put(
                f"/exam_schedule/confirm_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200

            assert response.json()["message"] == "Reservation confirmed successfully"

            session.refresh(reservation)
            confirmed_reservation = session.get(Reservation, 1)
            assert confirmed_reservation.confirmed

    class TestEditReservation:
        def test_edit_reservation_should_return_403_with_no_token(self, test_db):
            response = client.put(
                "/exam_schedule/edit_reservation/1",
            )

            assert response.status_code == 403, response.text

        def test_edit_reservation_should_return_403_with_invalid_token(self, test_db):
            response = client.put(
                "/exam_schedule/edit_reservation/1",

                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        @pytest.mark.parametrize("reservation_id", [1000, 999, -1])
        def test_edit_reservation_should_return_404_when_reservation_not_found(self, reservation_id, test_db):
            token = encode_jwt('1', 'client_user', 'client')

            response = client.put(
                f"/exam_schedule/edit_reservation/{reservation_id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"comment": "New Comment"}
            )

            assert response.status_code == 404

            assert response.json() == {"detail": "Reservation not found"}

        def test_edit_reservation_should_return_400_when_edit_confirmed_reservation(self,
                                                                                    test_db_with_users_and_exam_schedules):
            session = TestingSessionLocal()
            reservation = Reservation(user_id=1, comment="Old Comment", confirmed=True)
            session.add(reservation)
            session.flush()

            token = encode_jwt('2', 'admin_user', 'admin')

            response = client.put(
                f"/exam_schedule/edit_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"comment": "New Comment"}
            )

            assert response.status_code == 400

            assert response.json() == {"detail": "Cannot edit confirmed reservation"}

        def test_edit_reservation_client_editing_other_user_reservation(self, test_db_with_users_and_exam_schedules):
            session = TestingSessionLocal()
            reservation = Reservation(user_id=2, comment="Old Comment", confirmed=False)
            session.add(reservation)
            session.flush()

            token = encode_jwt('1', 'client_user', 'client')

            response = client.put(
                f"/exam_schedule/edit_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"comment": "New Comment"}
            )

            assert response.status_code == 403

            assert response.json() == {"detail": "Cannot edit other users' reservations"}

        def test_edit_reservation_success_for_client(self, test_db_with_users_and_exam_schedules):
            session = TestingSessionLocal()
            reservation = Reservation(user_id=1, comment="Old Comment", confirmed=False)
            session.add(reservation)
            session.flush()

            token = encode_jwt('1', 'client_user', 'client')

            new_comment = "New Comment"

            response = client.put(
                f"/exam_schedule/edit_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"comment": new_comment}
            )

            assert response.status_code == 200

            session.refresh(reservation)
            updated_reservation = session.get(Reservation, 1)

            assert updated_reservation.comment == new_comment

        def test_edit_reservation_success_for_admin(self, test_db_with_users_and_exam_schedules):
            session = TestingSessionLocal()
            reservation = Reservation(user_id=1, comment="Old Comment", confirmed=False)
            session.add(reservation)
            session.flush()

            token = encode_jwt('2', 'admin_user', 'admin')

            new_comment = "New Comment"

            response = client.put(
                f"/exam_schedule/edit_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"comment": new_comment}
            )

            assert response.status_code == 200

            session.refresh(reservation)
            updated_reservation = session.get(Reservation, 1)

            assert updated_reservation.comment == new_comment

    class TestDeleteReservation:
        def test_delete_reservation_should_return_403_with_no_token(self, test_db):
            response = client.delete(
                "/exam_schedule/delete_reservation/1",
            )

            assert response.status_code == 403, response.text

        def test_delete_reservation_should_return_403_with_invalid_token(self, test_db):
            response = client.delete(
                "/exam_schedule/delete_reservation/1",

                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        @pytest.mark.parametrize("reservation_id", [1000, 999, -1])
        def test_delete_reservation_should_return_404_when_not_found(self, reservation_id, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            response = client.delete(
                f"/exam_schedule/delete_reservation/{reservation_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 404

            assert response.json()["detail"] == "Reservation not found"

        def test_delete_reservation_should_return_403_client_delete_other_reservation(self,
                                                                                      test_db_with_users_and_exam_schedules):
            token = encode_jwt('1', 'user 1', 'client')

            session = TestingSessionLocal()
            reservation = Reservation(user_id=2, exam_schedule_id=1, confirmed=False)
            session.add(reservation)
            session.flush()

            response = client.delete(
                f"/exam_schedule/delete_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 403

            assert response.json()["detail"] == "Cannot delete this reservation"

        def test_delete_reservation_should_return_403_client_delete_confirmed_reservation(self,
                                                                                          test_db_with_users_and_exam_schedules):
            token = encode_jwt('1', 'user 1', 'client')

            session = TestingSessionLocal()
            reservation = Reservation(user_id=1, exam_schedule_id=1, confirmed=True)
            session.add(reservation)
            session.flush()

            response = client.delete(
                f"/exam_schedule/delete_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 403

            assert response.json()["detail"] == "Cannot delete this reservation"

        def test_delete_reservation_should_return_403_admin_delete_confirmed_reservation(self,
                                                                                         test_db_with_users_and_exam_schedules):
            token = encode_jwt('2', 'admin 1', 'admin')

            session = TestingSessionLocal()
            reservation = Reservation(user_id=1, exam_schedule_id=1, confirmed=True)
            session.add(reservation)
            session.flush()

            response = client.delete(
                f"/exam_schedule/delete_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 403

            assert response.json()["detail"] == "Cannot delete confirmed reservation"

        def test_delete_reservation_client_delete_success(self, test_db_with_users_and_exam_schedules):
            token = encode_jwt('1', 'user 1', 'client')

            session = TestingSessionLocal()
            reservation = Reservation(user_id=1, exam_schedule_id=1, confirmed=False)
            session.add(reservation)
            session.flush()

            response = client.delete(
                f"/exam_schedule/delete_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200, response.text

            assert response.json()["message"] == "Reservation deleted successfully"

            session.expire_all()
            deleted_reservation = session.get(Reservation, 1)
            assert deleted_reservation is None

        def test_delete_reservation_admin_delete_success(self, test_db_with_users_and_exam_schedules):
            token = encode_jwt('2', 'admin 1', 'admin')

            session = TestingSessionLocal()
            reservation = Reservation(user_id=1, exam_schedule_id=1, confirmed=False)
            session.add(reservation)
            session.flush()

            response = client.delete(
                f"/exam_schedule/delete_reservation/{reservation.id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200, response.text

            assert response.json()["message"] == "Reservation deleted successfully"

            session.expire_all()
            deleted_reservation = session.get(Reservation, 1)
            assert deleted_reservation is None


class TestUtil:
    def test_encode_jwt(self):
        token = encode_jwt('1', 'user 1', 'client')

        payload = decode_jwt(token)
        assert payload['id'] == '1'
        assert payload['user_id'] == 'user 1'
        assert payload['role'] == 'client'
