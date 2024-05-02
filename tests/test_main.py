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

    def insert_reservation_data(data: Tuple):
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
        response = client.post(
            "/users/login",
            json={
                "user_id": 'user 1',
                "password": '789456'
            }
        )
        assert response.status_code == 200, response.text
        data = response.json()

        assert 'token' in data.keys()

        token = data['token']

        payload = jwt.decode(token, JWT_SECRET, algorithms='HS256')
        assert payload['user_id'] == 'user 1'


class TestExamRoute:
    def test_get_exam_schedules_should_return_403_with_no_token(self, test_db):
        response = client.get(
            "/exam_schedule",
        )

        assert response.status_code == 403, response.text

    def test_get_exam_schedules_should_return_401_with_invalid_token(self, test_db):
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
        # Generate JWT token for a non-client user (e.g., admin)
        token = encode_jwt('1', 'admin 1', 'admin')

        # Send a POST request to the make_reservation endpoint
        response = client.post(
            "/exam_schedule/make_reservation/2",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert that the response status code is 403
        assert response.status_code == 403

    def test_make_reservation_should_return_400_when_user_already_has_reservation(self, test_db_with_users_and_exam_schedules):
        # Generate JWT token for a client user
        token = encode_jwt('1', 'user 1', 'client')

        # Mock an existing reservation for the user
        existing_reservation = Reservation(user_id='1', exam_schedule_id=1)
        session = TestingSessionLocal()

        session.add(existing_reservation)
        session.flush()

        # Send a POST request to the make_reservation endpoint
        response = client.post(
            "/exam_schedule/make_reservation/1",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert that the response status code is 400
        assert response.status_code == 400

    @pytest.mark.parametrize("exam_schedule_id", [1000, 999, -1])  # IDs that don't exist
    def test_make_reservation_exam_schedule_not_found(self, exam_schedule_id, test_db_with_users):
        # Generate JWT token for a client user
        token = encode_jwt('1', 'user 1', 'client')

        # Send a POST request to the make_reservation endpoint with a non-existent exam_schedule_id
        response = client.post(
            f"/exam_schedule/make_reservation/{exam_schedule_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert that the response status code is 404
        assert response.status_code == 404

        # Assert that the response contains the correct detail message
        assert response.json() == {"detail": "Exam schedule not found"}

    def test_make_reservation_max_reservation_reached(self, test_db_with_users):
        # Generate JWT token for a client user
        token = encode_jwt('1', 'user 1', 'client')

        # Add an exam schedule with maximum reservations
        exam_schedule = ExamSchedule(name="Example Exam", date_time=datetime.datetime.now(datetime.UTC))
        session = TestingSessionLocal()
        session.add(exam_schedule)

        session.commit()

        max_reservations = MAX_RESERVATION_NUM
        for i in range(max_reservations):
            reservation = Reservation(user_id='2', exam_schedule_id=exam_schedule.id, confirmed=True)
            session.add(reservation)

        session.commit()

        # Send a POST request to the make_reservation endpoint for the exam schedule with maximum reservations
        response = client.post(
            f"/exam_schedule/make_reservation/{exam_schedule.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert that the response status code is 400
        assert response.status_code == 400

        # Assert that the response contains the correct detail message
        assert response.json() == {"detail": "Exam schedule has reached maximum reservations"}

    def test_make_reservation_success(self, test_db_with_users):
        # Generate JWT token for a client user
        token = encode_jwt('1', 'user 1', 'client')

        # Add an exam schedule
        exam_schedule = ExamSchedule(name="Example Exam", date_time=datetime.datetime.now(datetime.UTC))
        session = TestingSessionLocal()
        session.add(exam_schedule)

        session.commit()

        # Send a POST request to the make_reservation endpoint
        response = client.post(
            f"/exam_schedule/make_reservation/{exam_schedule.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert that the response status code is 201
        assert response.status_code == 201

        # Assert that the response contains the newly created reservation
        assert "user_id" in response.json()
        assert "exam_schedule_id" in response.json()
        assert "confirmed" in response.json()
        assert response.json()["user_id"] == 1  # Assuming the user_id is '1' for the test case
        assert response.json()["exam_schedule_id"] == exam_schedule.id
        assert response.json()["confirmed"] is False  # Assuming the reservation is not confirmed initially


class TestUtil:
    def test_encode_jwt(self):
        token = encode_jwt('1', 'user 1', 'client')

        payload = decode_jwt(token)
        assert payload['id'] == '1'
        assert payload['user_id'] == 'user 1'
        assert payload['role'] == 'client'
