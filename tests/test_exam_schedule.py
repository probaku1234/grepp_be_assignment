from db.models import Reservation, ExamSchedule
from tests.test_main import client, test_db_with_users, test_db, UtilTest, TestingSessionLocal
from util import encode_jwt, decode_jwt
import datetime


class TestExamScheduleRoute:
    class TestGetSchedules:
        def test_get_exam_schedules_should_return_403_with_no_token(self, test_db):
            response = client.get(
                "/api/v1/exam_schedule",
            )

            assert response.status_code == 403, response.text

        def test_get_exam_schedules_should_return_403_with_invalid_token(self, test_db):
            response = client.get(
                "/api/v1/exam_schedule",
                headers={
                    "Authorization": "Bearer invalid_token"
                }
            )

            assert response.status_code == 403, response.text

        def test_get_exam_schedules_should_return_empty_list_with_no_exam_schedule_data(self, test_db_with_users):
            token = encode_jwt('1', 'user 1', 'client')

            response = client.get(
                "/api/v1/exam_schedule",
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
                days=1), datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=2)))
            UtilTest.insert_exam_schedule_data((2, 'exam 2', datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=5), datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=7)))

            response = client.get(
                "/api/v1/exam_schedule",
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
                days=1), datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=2)))
            UtilTest.insert_exam_schedule_data((2, 'exam 2', datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=5), datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=7)))
            UtilTest.insert_exam_schedule_data(
                (3, 'exam 3', datetime.datetime(2022, 2, 3), datetime.datetime(2022, 4, 3)))

            response = client.get(
                "/api/v1/exam_schedule",
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
                                         start_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                             days=2),
                                         end_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                             days=5))
            session.add(exam_schedule)

            session.commit()

            reservation = Reservation(id=1, user_id='1', exam_schedule_id=exam_schedule.id, confirmed=True)
            session.add(reservation)
            session.commit()

            response = client.get(
                "/api/v1/exam_schedule",
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
                                         start_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                             days=2),
                                         end_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                             days=5)
                                         )
            session.add(exam_schedule)

            session.commit()

            reservation = Reservation(id=1, user_id='2', exam_schedule_id=exam_schedule.id, confirmed=True)
            session.add(reservation)
            session.commit()

            response = client.get(
                "/api/v1/exam_schedule",
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
            "/api/v1/exam_schedule",
        )

        assert response.status_code == 403, response.text

    def test_create_exam_schedule_should_return_401_with_invalid_token(self, test_db):
        response = client.post(
            "/api/v1/exam_schedule",
            headers={
                "Authorization": "Bearer invalid_token"
            }
        )

        assert response.status_code == 403, response.text

    def test_create_exam_schedule_should_return_403_for_non_admin_user(self, test_db_with_users):
        token = encode_jwt('1', 'client 1', 'client')

        response = client.post(
            "/api/v1/exam_schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": 'test test',
                "start_time": '2025-02-20 12:30',
                "end_time": '2025-03-20 12:30'
            }
        )

        assert response.status_code == 403

    def test_create_exam_schedule_should_return_422_when_past_date_given(self, test_db_with_users):
        token = encode_jwt('2', 'admin 1', 'admin')

        response = client.post(
            "/api/v1/exam_schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": 'test test',
                "start_time": '1990-02-20 12:30',
                "end_time": '1990-03-20 12:30'
            }
        )

        assert response.status_code == 422, response.text
        assert response.json()['detail'][0]['msg'] == 'Input should be in the future'

    def test_create_exam_schedule_should_return_422_when_required_fields_not_given(self, test_db_with_users):
        token = encode_jwt('2', 'admin 1', 'admin')

        response = client.post(
            "/api/v1/exam_schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "start_time": '1990-02-20 12:30'
            }
        )

        assert response.status_code == 422, response.text
        assert response.json()['detail'][0]['msg'] == 'Field required'

    def test_create_exam_schedule_should_return_422_when_end_time_is_smaller_than_start_time(self, test_db_with_users):
        token = encode_jwt('2', 'admin 1', 'admin')

        response = client.post(
            "/api/v1/exam_schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "test_name",
                "start_time": '2025-02-20 12:30',
                "end_time": '2025-01-20 12:30'
            }
        )

        assert response.status_code == 422, response.text
        assert response.json()['detail'][0]['msg'] == 'Value error, end time must be greater than the start time'

    def test_create_exam_schedule_should_return_400_when_name_already_exist(self, test_db_with_users):
        token = encode_jwt('2', 'admin 1', 'admin')

        test_name = 'test test'
        session = TestingSessionLocal()
        new_exam_schedule = ExamSchedule(
            name=test_name,
            start_time=datetime.datetime.now(datetime.UTC),
            end_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                days=2)
        )
        session.add(new_exam_schedule)
        session.flush()

        response = client.post(
            "/api/v1/exam_schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": test_name,
                "start_time": '2025-02-20 12:30',
                "end_time": '2025-03-20 12:30'
            }
        )

        assert response.status_code == 400, response.text
        assert response.json()['detail'] == "Exam schedule's name must be unique. Please use other name."

    def test_create_exam_schedule_success(self, test_db_with_users):
        token = encode_jwt('2', 'admin 1', 'admin')

        test_name = 'test test'
        test_date = '2025-02-20 12:30'

        response = client.post(
            "/api/v1/exam_schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": test_name,
                "start_time": '2025-02-20 12:30',
                "end_time": '2025-03-20 12:30'
            }
        )

        assert response.status_code == 201, response.text

        session = TestingSessionLocal()
        created_exam_schedule = session.get(ExamSchedule, 1)
        assert created_exam_schedule.name == test_name
        assert created_exam_schedule.start_time == datetime.datetime.strptime(test_date, '%Y-%m-%d %H:%M')
