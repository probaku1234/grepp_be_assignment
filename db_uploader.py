""""
테스트용 유저 데이터를 만드는 데 사용됩니다. `users.csv`에서 데이터를 가져옵니다.
"""

from sqlalchemy.engine.interfaces import DBAPICursor
from sqlalchemy.dialects.postgresql import insert
from database import engine, Base
import csv
from dotenv import load_dotenv
import os
import datetime

load_dotenv()


def _insert_user(data, cursor: DBAPICursor):
    query = 'INSERT INTO users(id, user_id, password, role) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;'

    cursor.execute(query, data)


def init_data():
    if os.environ.get('environment', 'dev') == 'test':
        return

    with open('data/users.csv', 'r', encoding='utf-8') as data:
        print('---inserting user data started---')
        conn = engine.raw_connection()

        cursor = conn.cursor()
        data = csv.reader(data)

        for line in data:
            _insert_user(line, cursor)

        print('---inserting user data ended---')
        conn.commit()

    with engine.connect() as conn:
        exam_table = Base.metadata.tables['exam_schedules']

        exam1_insert_stmt = insert(exam_table).values(name='exam 1',
                                                      date_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                                          days=2)).on_conflict_do_nothing()
        exam2_insert_stmt = insert(exam_table).values(name='exam 2',
                                                      date_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                                                          days=5)).on_conflict_do_nothing()

        conn.execute(exam1_insert_stmt)
        conn.execute(exam2_insert_stmt)
        conn.commit()
