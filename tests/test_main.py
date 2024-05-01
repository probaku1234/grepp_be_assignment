import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv
import os
from typing import Tuple

from database import Base, get_db
from main import app
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


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

JWT_SECRET = os.environ.get('JWT_SECRET')


class TestUser:
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


class TestUtil:
    def test_encode_jwt(self):
        token = encode_jwt('user 1', 'client')

        payload = decode_jwt(token)
        assert payload['user_id'] == 'user 1'
        assert payload['role'] == 'client'
