from db.models import Reservation, ExamSchedule, User
from tests.test_main import client, test_db_with_users, test_db, UtilTest, TestingSessionLocal, \
    test_db_with_users_and_exam_schedules
from util import encode_jwt
from service.exam_schedule_service import MAX_RESERVATION_NUM
import pytest
import datetime


class TestReservationRoute:
    class TestMakeReservation:
        def test_make_reservation_should_return_403_with_no_token(self, test_db):
            response = client.post(
                "/api/v1/exam_schedule/make_reservation/2",
            )

            assert response.status_code == 403, response.text

        def test_make_reservation_should_return_401_with_invalid_token(self, test_db):
            response = client.post(
                "/api/v1/exam_schedule/make_reservation/2",
                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        def test_make_reservation_should_return_403_for_non_client_user(self, test_db_with_users):
            token = encode_jwt('1', 'admin 1', 'admin')

            response = client.post(
                "/api/v1/exam_schedule/make_reservation/2",
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
                "/api/v1/exam_schedule/make_reservation/1",
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
                f"/api/v1/exam_schedule/make_reservation/{exam_schedule_id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    'comment': ""
                }
            )

            assert response.status_code == 404

            assert response.json() == {"detail": "Exam schedule not found"}

        def test_make_reservation_max_reservation_reached(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            exam_schedule = ExamSchedule(name="Example Exam",
                                         start_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                             days=2),
                                         end_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                             days=5))
            session = TestingSessionLocal()
            session.add(exam_schedule)

            session.commit()

            max_reservations = MAX_RESERVATION_NUM
            for i in range(max_reservations):
                user = User(user_id=f"test user {i}", password="123123123", role="client")
                session.add(user)

            session.commit()

            test_users = session.query(User).filter(User.id != 1, User.role.contains('client')).all()

            for user in test_users:
                reservation = Reservation(user_id=user.id, exam_schedule_id=exam_schedule.id, confirmed=True)
                session.add(reservation)

            session.commit()

            response = client.post(
                f"/api/v1/exam_schedule/make_reservation/{exam_schedule.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    'comment': ""
                }
            )

            assert response.status_code == 400

            assert response.json() == {"detail": "Exam schedule has reached maximum reservations"}

        def test_make_reservation_success(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            exam_schedule = ExamSchedule(name="Example Exam",
                                         start_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                             days=2),
                                         end_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                             days=5))
            session = TestingSessionLocal()
            session.add(exam_schedule)

            session.commit()

            test_comment = "test comment"

            response = client.post(
                f"/api/v1/exam_schedule/make_reservation/{exam_schedule.id}",
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
            "/api/v1/exam_schedule/my_reservation",
        )

        assert response.status_code == 403, response.text

    def test_my_reservation_should_return_403_with_invalid_token(self, test_db):
        response = client.get(
            "/api/v1/exam_schedule/my_reservation",

            headers={
                "Authorization": "Bearer invalid_token"
            }
        )

        assert response.status_code == 403, response.text

    def test_my_reservation_should_return_empty_list_with_no_reservation_data(self, test_db_with_users):
        token = encode_jwt('1', 'user 1', 'client')

        response = client.get(
            "/api/v1/exam_schedule/my_reservation",
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
            "/api/v1/exam_schedule/my_reservation",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        assert response.status_code == 403, response.text
        assert response.json()["detail"] == "Only clients can view their reservations"

    def test_my_reservation_should_return_current_user_reservations(self, test_db_with_users_and_exam_schedules):
        token = encode_jwt('1', 'user 1', 'client')

        session = TestingSessionLocal()
        test_user_id = 1
        test_exam_schedule_id = [1, 2]
        reservations_data = [
            {"user_id": test_user_id, "exam_schedule_id": test_exam_schedule_id[0]},
            {"user_id": test_user_id, "exam_schedule_id": test_exam_schedule_id[1]}
        ]
        for reservation_data in reservations_data:
            reservation = Reservation(**reservation_data)
            session.add(reservation)
        session.flush()

        response = client.get(
            "/api/v1/exam_schedule/my_reservation",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

        for item in response_data:
            assert "user_id" in item
            assert "exam_schedule_id" in item
            assert item['user_id'] == test_user_id
            assert item['exam_schedule_id'] in test_exam_schedule_id


class TestGetUserReservations:
    def test_get_user_reservations_should_return_403_with_no_token(self, test_db):
        response = client.get(
            "/api/v1/exam_schedule/user_reservation/1",
        )

        assert response.status_code == 403, response.text

    def test_get_user_reservations_should_return_403_with_invalid_token(self, test_db):
        response = client.get(
            "/api/v1/exam_schedule/user_reservation/1",

            headers={
                "Authorization": "Bearer invalid_token"
            }
        )

        assert response.status_code == 403, response.text

    def test_get_user_reservations_should_return_403_for_client(self, test_db_with_users):
        token = encode_jwt('1', 'user 1', 'client')

        response = client.get(
            "/api/v1/exam_schedule/user_reservation/1",
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
            f"/api/v1/exam_schedule/user_reservation/{invalid_user_id}",
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
            "/api/v1/exam_schedule/user_reservation/1",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

    class TestConfirmReservations:
        def test_confirm_reservation_should_return_403_with_no_token(self, test_db):
            response = client.put(
                "/api/v1/reservation/confirm_reservation",
            )

            assert response.status_code == 403, response.text

        def test_confirm_reservation_should_return_403_with_invalid_token(self, test_db):
            response = client.put(
                "/api/v1/reservation/confirm_reservation",

                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        def test_confirm_reservation_should_return_403_for_client(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            response = client.put(
                "/api/v1/reservation/confirm_reservation",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    'user_id': 3,
                    'exam_schedule_id': 4,
                }
            )

            assert response.status_code == 403, response.text
            assert response.json()["detail"] == "Only admins can confirm reservations"

        @pytest.mark.parametrize("exam_schedule_id", [1000, 999, -1])
        def test_confirm_reservation_should_return_404_reservation_not_found(self, exam_schedule_id,
                                                                             test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            response = client.put(
                f"/api/v1/reservation/confirm_reservation",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    'user_id': 1,
                    'exam_schedule_id': exam_schedule_id,
                }
            )

            assert response.status_code == 404

            assert response.json()["detail"] == "Reservation not found"

        def test_confirm_reservation_already_confirmed(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            test_user_id = 2
            test_exam_schedule_id = 1

            session = TestingSessionLocal()
            reservation = Reservation(user_id=test_user_id, exam_schedule_id=test_exam_schedule_id, confirmed=True)
            session.add(reservation)
            session.flush()

            response = client.put(
                f"/api/v1/reservation/confirm_reservation",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    'user_id': test_user_id,
                    'exam_schedule_id': test_exam_schedule_id,
                }
            )

            assert response.status_code == 400

            assert response.json()["detail"] == "Reservation already confirmed"

        def test_confirm_reservation_success(self, test_db_with_users):
            token = encode_jwt('2', 'admin 1', 'admin')

            test_user_id = 2
            test_exam_schedule_id = 1

            session = TestingSessionLocal()
            reservation = Reservation(user_id=test_user_id, exam_schedule_id=test_exam_schedule_id, confirmed=False)
            session.add(reservation)
            session.flush()

            response = client.put(
                f"/api/v1/reservation/confirm_reservation",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    'user_id': test_user_id,
                    'exam_schedule_id': test_exam_schedule_id,
                }
            )

            assert response.status_code == 200

            assert response.json()["message"] == "Reservation confirmed successfully"

            session.refresh(reservation)
            confirmed_reservation = session.get(Reservation, (test_user_id, test_exam_schedule_id))
            assert confirmed_reservation.confirmed
